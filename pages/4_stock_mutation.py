import pandas as pd
import streamlit as st
import database
import data_processor
import playwright_engine
from utils import (
    make_solid_box, render_footer,
    check_auth, render_indicators, render_header,
    send_telegram_alert, init_session_state, render_wakelock, style_status, render_aggrid,
)

# --- AUTH CHECK ---
check_auth()

supabase = database.init_supabase()
_sys_cfg = database.get_system_config(supabase)
REASON_CODE = _sys_cfg["REASON_CODE"]
WAREHOUSE   = _sys_cfg["WAREHOUSE"]
URL_LOGIN   = _sys_cfg["URL_LOGIN"]
TIMEOUT_MS  = _sys_cfg["TIMEOUT_MS"]
TABLE_UPDATE_INTERVAL = _sys_cfg["TABLE_UPDATE_INTERVAL"]

# --- STATE MANAGEMENT ---
init_session_state(
    is_mutasi_running=False,
    mutasi_review_df=None,
    mutasi_file_id=None,
)

render_wakelock()

# --- MAIN UI ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_mutasi_running else "STANDBY"

render_indicators(db_status, bot_status, bot_type="MUTASI ENGINE")
render_header("Mutasi Stock", st.session_state.current_user)

# --- DISTRIBUTOR SELECTION ---
col1, col2 = st.columns(2)

list_dist = database.get_distributor_list(supabase)

with col1:
    with st.container(border=True):
        st.markdown("<div class='box-np'>Distributor Pengirim (Stock Dikurangi)</div>", unsafe_allow_html=True)
        dist_a = st.selectbox("Pilih Distributor Pengirim", list_dist, key="mutasi_dist_a")
        bot_user_a, bot_pass_a = database.get_distributor_creds(supabase, dist_a)
        if bot_user_a:
            st.text_input("NP User ID", value=bot_user_a, disabled=True, key="mutasi_user_a")
            st.text_input("NP Password", value="********", type="password", disabled=True, key="mutasi_pass_a")

with col2:
    with st.container(border=True):
        st.markdown("<div class='box-dist'>Distributor Penerima (Stock Ditambah)</div>", unsafe_allow_html=True)
        # Filter out dist_a from receiver list to prevent same-distributor selection
        list_dist_b = [d for d in list_dist if d != dist_a]
        dist_b = st.selectbox("Pilih Distributor Penerima", list_dist_b, key="mutasi_dist_b")
        bot_user_b, bot_pass_b = database.get_distributor_creds(supabase, dist_b)
        if bot_user_b:
            st.text_input("NP User ID", value=bot_user_b, disabled=True, key="mutasi_user_b")
            st.text_input("NP Password", value="********", type="password", disabled=True, key="mutasi_pass_b")

# --- FILE UPLOAD + COLUMN MAPPING ---
with st.container(border=True):
    st.markdown("<div class='box-np'>Transfer File (dari Distributor Pengirim)</div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload file Excel berisi SKU yang akan dimutasi", type=['csv', 'xlsx'], key="mutasi_file_uploader")

    # Track file changes to reset state
    curr_file_id = getattr(uploaded_file, "file_id", uploaded_file.name if uploaded_file else None) if uploaded_file else None
    if curr_file_id != st.session_state.mutasi_file_id:
        st.session_state.mutasi_file_id = curr_file_id
        st.session_state.mutasi_review_df = None

if uploaded_file is not None:
    df_raw = data_processor.load_data(uploaded_file)

    if df_raw is not None and not df_raw.empty:
        st.markdown(make_solid_box(f"File loaded — {len(df_raw)} rows, {len(df_raw.columns)} columns", "#3b82f6", "#3b82f6"), unsafe_allow_html=True)

        # --- COLUMN MAPPING ---
        st.markdown("<div class='box-review'>Column Mapping</div>", unsafe_allow_html=True)
        mc1, mc2, mc3 = st.columns(3)

        with mc1:
            # Auto-detect SKU column
            sku_candidates = [c for c in df_raw.columns if any(k in str(c).lower() for k in ['sku', 'code', 'kode', 'produk'])]
            idx_sku = df_raw.columns.get_loc(sku_candidates[0]) if sku_candidates else 0
            sku_col = st.selectbox("SKU Column", df_raw.columns, index=idx_sku, key="mutasi_sku_col")

        with mc2:
            # Auto-detect Description column
            desc_candidates = [c for c in df_raw.columns if any(k in str(c).lower() for k in ['desc', 'name', 'nama', 'produk'])]
            idx_desc = df_raw.columns.get_loc(desc_candidates[0]) if desc_candidates else (1 if len(df_raw.columns) > 1 else 0)
            desc_col = st.selectbox("Description Column", df_raw.columns, index=idx_desc, key="mutasi_desc_col")

        with mc3:
            # Auto-detect Qty column
            qty_candidates = [c for c in df_raw.columns if any(k in str(c).lower() for k in ['qty', 'stock', 'stok', 'jumlah', 'mutasi'])]
            idx_qty = df_raw.columns.get_loc(qty_candidates[0]) if qty_candidates else (2 if len(df_raw.columns) > 2 else 0)
            qty_col = st.selectbox("Qty Column", df_raw.columns, index=idx_qty, key="mutasi_qty_col")

        # --- BUILD REVIEW TABLE ---
        df_review = df_raw[[sku_col, desc_col, qty_col]].copy()
        df_review.columns = ['SKU', 'Description', 'Qty']

        # Clean data
        df_review = df_review.dropna(subset=['SKU'])
        df_review['SKU'] = df_review['SKU'].astype(str).str.split('.').str[0].str.strip()
        df_review = df_review[~df_review['SKU'].str.lower().isin(['nan', 'none', '', 'total', 'grand total'])]
        df_review['Qty'] = pd.to_numeric(
            df_review['Qty'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
            errors='coerce'
        ).fillna(0).astype(int)
        df_review = df_review[df_review['Qty'] != 0].reset_index(drop=True)

        if len(df_review) > 0:
            st.session_state.mutasi_review_df = df_review

            # Summary metrics
            sm1, sm2, sm3 = st.columns(3)
            with sm1:
                st.markdown(f'''<div class="metric-box-match"><div class="metric-label">Total SKU</div><div class="metric-value">{len(df_review)}</div></div>''', unsafe_allow_html=True)
            with sm2:
                st.markdown(f'''<div class="metric-box-mismatch"><div class="metric-label">Total Qty Dikurangi ({dist_a})</div><div class="metric-value">-{df_review['Qty'].sum()}</div></div>''', unsafe_allow_html=True)
            with sm3:
                st.markdown(f'''<div class="metric-box-match"><div class="metric-label">Total Qty Ditambah ({dist_b})</div><div class="metric-value">+{df_review['Qty'].sum()}</div></div>''', unsafe_allow_html=True)

            # Review table with deduction/addition preview
            df_display = df_review.copy()
            df_display[f'Deduct ({dist_a})'] = df_display['Qty'].apply(lambda x: f"-{abs(x)}")
            df_display[f'Add ({dist_b})'] = df_display['Qty'].apply(lambda x: f"+{abs(x)}")

            st.markdown("<div class='box-review'>Stock Review</div>", unsafe_allow_html=True)
            render_aggrid(df_display[['SKU', 'Description', 'Qty', f'Deduct ({dist_a})', f'Add ({dist_b})']], key="mutasi_review", enable_filters=True)
        else:
            st.warning("Tidak ada SKU valid di file yang diupload.")
    else:
        st.error("Gagal memuat file. Pastikan format Excel/CSV benar.")

# --- EXECUTE ---
review_ready = st.session_state.mutasi_review_df is not None and len(st.session_state.mutasi_review_df) > 0
can_execute = review_ready and bot_user_a and bot_pass_a and bot_user_b and bot_pass_b and not st.session_state.is_mutasi_running

if st.button("EXECUTE MUTASI", type="primary", width="stretch", disabled=not can_execute):
    st.session_state.is_mutasi_running = True

    df_mutasi = st.session_state.mutasi_review_df.copy()

    # Dual layout
    st.markdown("<div class='box-review'>Execution</div>", unsafe_allow_html=True)
    exec_col1, exec_col2 = st.columns(2)

    with exec_col1:
        st.markdown(f"<div class='box-np'>DEDUCT: {dist_a} ({bot_user_a})</div>", unsafe_allow_html=True)
        table_a_ph = st.empty()
        prog_a_ph = st.empty()

    with exec_col2:
        st.markdown(f"<div class='box-dist'>ADD: {dist_b} ({bot_user_b})</div>", unsafe_allow_html=True)
        table_b_ph = st.empty()
        prog_b_ph = st.empty()

    # Initial table render
    df_a_display = df_mutasi[['SKU', 'Description', 'Qty']].copy()
    df_a_display['Qty'] = '-' + df_a_display['Qty'].astype(str)
    df_a_display['Status'] = 'Pending'
    df_a_display['Keterangan'] = 'Ready'
    render_aggrid(df_a_display, key="mutasi_exec_a", live_update=True)

    df_b_display = df_mutasi[['SKU', 'Description', 'Qty']].copy()
    df_b_display['Status'] = 'Pending'
    df_b_display['Keterangan'] = 'Ready'
    render_aggrid(df_b_display, key="mutasi_exec_b", live_update=True)

    prog_a_ph.progress(0)
    prog_b_ph.progress(0)

    # Terminal log placeholders
    log_label_a_ph = st.empty()
    log_a_ph = st.empty()
    log_label_b_ph = st.empty()
    log_b_ph = st.empty()

    log_label_a_ph.markdown(f"""
        <div style='display: inline-block; margin-bottom: 4px;'>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>System Activity</span>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #e5e5e5; text-transform: uppercase; letter-spacing: 0.1em;'>DEDUCT LOG — {dist_a}</span>
        </div>
    """, unsafe_allow_html=True)

    log_label_b_ph.markdown(f"""
        <div style='display: inline-block; margin-bottom: 4px;'>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #f87171; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>System Activity</span>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #e5e5e5; text-transform: uppercase; letter-spacing: 0.1em;'>ADD LOG — {dist_b}</span>
        </div>
    """, unsafe_allow_html=True)

    # Execute — engine handles log rendering internally
    playwright_engine.run_mutasi_execution(
        df_mutasi,
        bot_user_a, bot_pass_a, dist_a,
        bot_user_b, bot_pass_b, dist_b,
        URL_LOGIN, TIMEOUT_MS, WAREHOUSE,
        REASON_CODE, TABLE_UPDATE_INTERVAL,
        send_telegram_alert,
        table_a_ph, table_b_ph,
        prog_a_ph, prog_b_ph,
        log_a_ph, log_b_ph,
        supabase,
    )

    # Clear review state after execution
    st.session_state.mutasi_review_df = None

render_footer()
