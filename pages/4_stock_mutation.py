import pandas as pd
import streamlit as st
import utils
import database
import data_processor
import playwright_engine
from database import EXCLUDE_PREFIX
from utils import (
    render_footer, make_solid_box, render_metric_card,
    check_auth, render_indicators, render_header,
    send_telegram_alert, init_session_state, render_wakelock,
    safe_parse_numeric,
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
    selected_reason_code="",
    remark_text=""
)

render_wakelock()

# --- MAIN UI ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_mutasi_running else "STANDBY"

render_indicators(db_status, bot_status, bot_type="MUTASI ENGINE")
render_header("Mutasi Stock", st.session_state.current_user)

@st.dialog("Panduan Pengguna - Mutasi Stock")
def show_user_guide():
    st.markdown("""
    **Cara Penggunaan:**
    1. Pilih **Distributor Pengirim** dan **Distributor Penerima**. Keduanya harus berbeda.
    2. Unggah file Excel/CSV berisi daftar SKU dan jumlah (Qty) yang akan dimutasi.
    3. Sesuaikan **Column Mapping** (SKU, Description, Qty) jika sistem tidak mendeteksinya secara otomatis.
    4. Periksa **Stock Review** untuk memastikan daftar SKU, jumlah pengurang (Deduct), dan penambah (Add) sudah tepat.
    5. Pilih **Reason Adjustment** dan tambahkan **Remark** opsional.
    6. Klik **Execute** untuk memproses mutasi. Pastikan Anda tidak menutup browser hingga log eksekusi pada pengirim maupun penerima telah selesai 100%.
    """)

st.markdown("<div class='guide-anchor'></div>", unsafe_allow_html=True)
if st.button(":material/help: Panduan", type="secondary"):
    show_user_guide()

# --- DISTRIBUTOR SELECTION ---
col1, col2 = st.columns(2)

list_dist = database.get_distributor_list(supabase)

with col1:
    st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
    with st.container(border=True):
        dist_a = st.selectbox("Pilih Distributor Pengirim", list_dist, key="mutasi_dist_a")
        bot_user_a, bot_pass_a = database.get_distributor_creds(supabase, dist_a)

with col2:
    st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
    with st.container(border=True):
        # Filter out dist_a from receiver list to prevent same-distributor selection
        list_dist_b = [d for d in list_dist if d != dist_a]
        dist_b = st.selectbox("Pilih Distributor Penerima", list_dist_b, key="mutasi_dist_b")
        bot_user_b, bot_pass_b = database.get_distributor_creds(supabase, dist_b)

# --- FILE UPLOAD + COLUMN MAPPING ---
st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True):
    uploaded_file = st.file_uploader("Upload file Excel berisi SKU yang akan dimutasi", type=['csv', 'xlsx'], key="mutasi_file_uploader")

    # Track file changes to reset state
    curr_file_id = getattr(uploaded_file, "file_id", uploaded_file.name if uploaded_file else None) if uploaded_file else None
    if curr_file_id != st.session_state.mutasi_file_id:
        st.session_state.mutasi_file_id = curr_file_id
        st.session_state.mutasi_review_df = None

if uploaded_file is not None:
    df_raw = data_processor.load_data(uploaded_file)

    if df_raw is not None and not df_raw.empty:
        st.markdown(f"""
            <style>
                div[data-testid="stFileUploader"] section {{ display: none !important; }}
                div[data-testid="stFileUploader"] {{ margin-bottom: -1rem !important; padding-bottom: 0px !important; }}
            </style>
            {make_solid_box(f"FILE LOADED: {uploaded_file.name}", "#FFDE59", "#0F172A")}
        """, unsafe_allow_html=True)
        if st.button("HAPUS FILE", type="secondary", use_container_width=True, icon=":material/delete:"):
            st.session_state.mutasi_file_uploader = None
            st.session_state.mutasi_file_id = None
            st.rerun()

        # --- COLUMN MAPPING ---
        st.subheader("Column Mapping")
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
        TARGET_SKUS = database.get_target_skus(supabase)
        df_review = data_processor.clean_sku_column(df_review, 'SKU', TARGET_SKUS)
        df_review['Qty'] = df_review['Qty'].apply(safe_parse_numeric).astype(int)
        df_review = df_review[df_review['Qty'] != 0].reset_index(drop=True)

        if len(df_review) > 0:
            st.session_state.mutasi_review_df = df_review

            # Summary metrics
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.markdown(render_metric_card("Total SKU", len(df_review)), unsafe_allow_html=True)
            with mc2:
                st.markdown(render_metric_card(f"Total Qty Dikurangi ({dist_a})", f"-{df_review['Qty'].sum()}"), unsafe_allow_html=True)
            with mc3:
                st.markdown(render_metric_card(f"Total Qty Ditambah ({dist_b})", f"+{df_review['Qty'].sum()}"), unsafe_allow_html=True)

            # Review table with deduction/addition preview
            df_display = df_review.copy()
            df_display[f'Deduct ({dist_a})'] = df_display['Qty'].apply(lambda x: f"-{abs(x)}")
            df_display[f'Add ({dist_b})'] = df_display['Qty'].apply(lambda x: f"+{abs(x)}")

            st.subheader("Stock Review")
            utils.render_neo_table(df_display[['SKU', 'Description', 'Qty', f'Deduct ({dist_a})', f'Add ({dist_b})']])
        else:
            st.warning("Tidak ada SKU valid di file yang diupload.")
    else:
        st.error("Gagal memuat file. Pastikan format Excel/CSV benar.")

# --- EXECUTE ---
review_ready = st.session_state.mutasi_review_df is not None and len(st.session_state.mutasi_review_df) > 0
can_execute = review_ready and bot_user_a and bot_pass_a and bot_user_b and bot_pass_b and not st.session_state.is_mutasi_running

st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True):
    reason_options = {
        "SA1": "SA1 - Transformasi Kode Barang",
        "SA2": "SA2 - Selisih Barang",
        "SA3": "SA3 - Transfer Gudang Internal",
        "SA4": "SA4 - Transfer Gudang External"
    }
    default_reason_idx = 0
    for i, key in enumerate(reason_options.keys()):
        if key == REASON_CODE:
            default_reason_idx = i
            break
    selected_reason_label = st.selectbox("Reason Adjustment", list(reason_options.values()), index=default_reason_idx, key="mutasi_reason")
    selected_reason_code = [k for k, v in reason_options.items() if v == selected_reason_label][0]
    remark_text = st.text_input("Remark", max_chars=50, key="mutasi_remark")
    
st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
execute_clicked = st.button("Execute", type="primary", use_container_width=True, disabled=not can_execute, icon=":material/play_arrow:")

if execute_clicked:
    st.session_state.is_mutasi_running = True
    st.session_state.selected_reason_code = selected_reason_code
    st.session_state.remark_text = remark_text
    st.rerun()

if st.session_state.is_mutasi_running:
    df_mutasi = st.session_state.mutasi_review_df.copy()

    # Dual layout
    exec_col1, exec_col2 = st.columns(2)

    with exec_col1:
        st.markdown(f"""
            <div style='border-left: 4px solid #FF2B2B; padding-left: 10px; margin-bottom: 14px; margin-top: 10px;'>
                <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 0.85rem; font-weight: 700; color: #FF2B2B; letter-spacing: 0.05em; text-transform: uppercase; display: block; line-height: 1.2;'>Deduct</span>
                <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 0.72rem; font-weight: 600; color: #808495; text-transform: uppercase; letter-spacing: 0.02em;'>{dist_a} ({bot_user_a})</span>
            </div>
        """, unsafe_allow_html=True)
        table_a_ph = st.empty()
        prog_a_ph = st.empty()

    with exec_col2:
        st.markdown(f"""
            <div style='border-left: 4px solid #09A53C; padding-left: 10px; margin-bottom: 14px; margin-top: 10px;'>
                <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 0.85rem; font-weight: 700; color: #09A53C; letter-spacing: 0.05em; text-transform: uppercase; display: block; line-height: 1.2;'>Add</span>
                <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 0.72rem; font-weight: 600; color: #808495; text-transform: uppercase; letter-spacing: 0.02em;'>{dist_b} ({bot_user_b})</span>
            </div>
        """, unsafe_allow_html=True)
        table_b_ph = st.empty()
        prog_b_ph = st.empty()

    # Initial table render
    df_a_display = df_mutasi[['SKU', 'Description', 'Qty']].copy()
    df_a_display['Qty'] = '-' + df_a_display['Qty'].astype(str)
    df_a_display['Status'] = 'Pending'
    df_a_display['Keterangan'] = 'Ready'
    utils.render_neo_table(table_a_ph, df_a_display)

    df_b_display = df_mutasi[['SKU', 'Description', 'Qty']].copy()
    df_b_display['Status'] = 'Pending'
    df_b_display['Keterangan'] = 'Ready'
    utils.render_neo_table(table_b_ph, df_b_display)

    prog_a_ph.progress(0)
    prog_b_ph.progress(0)

    # Terminal log placeholders
    log_label_a_ph = st.empty()
    log_a_ph = st.empty()
    log_label_b_ph = st.empty()
    log_b_ph = st.empty()



    # Execute — engine handles log rendering internally
    try:
        playwright_engine.run_mutasi_execution(
            df_mutasi,
            bot_user_a, bot_pass_a, dist_a,
            bot_user_b, bot_pass_b, dist_b,
            URL_LOGIN, TIMEOUT_MS, WAREHOUSE, WAREHOUSE,
            st.session_state.selected_reason_code, TABLE_UPDATE_INTERVAL,
            send_telegram_alert,
            table_a_ph, table_b_ph,
            prog_a_ph, prog_b_ph,
            log_a_ph, log_b_ph,
            supabase,
            remark_text=st.session_state.remark_text,
            current_user=st.session_state.current_user,
        )
    finally:
        st.session_state.is_mutasi_running = False
        # Clear review state after execution
        st.session_state.mutasi_review_df = None


render_footer()
