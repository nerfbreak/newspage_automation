import pandas as pd
import streamlit as st
import utils
import database
import playwright_engine
from database import EXCLUDE_PREFIX
from utils import (
    render_footer, make_solid_box, render_metric_card,
    check_auth, render_indicators, render_header,
    encode_param, send_telegram_alert,
    init_session_state, render_wakelock,
    make_terminal_logger,
    resolve_distributor_url, safe_parse_numeric,
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
    initial_stock_df=None,
    initial_stock_raw=None,
    is_initial_running=False,
)

render_wakelock()

# --- MAIN UI ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_initial_running else "STANDBY"

render_indicators(db_status, bot_status, bot_type="INITIAL STOCK ENGINE")
render_header("Initial Stock", st.session_state.current_user)

# --- DISTRIBUTOR SELECTION ---
st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True):
    list_dist = database.get_distributor_list(supabase)
    _, default_index = resolve_distributor_url(list_dist)

    selected_distributor = st.selectbox("Pilih Distributor", list_dist, index=default_index, key="init_stock_dist")
    st.query_params.clear()
    st.query_params["d"] = encode_param(selected_distributor)
    bot_user, bot_pass = database.get_distributor_creds(supabase, selected_distributor)

# --- STEP 1: UPLOAD FILE ---
st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True):
    uploaded_file = st.file_uploader(
        "Upload file with SKU and Qty columns (csv, xlsx)",
        type=['csv', 'xlsx'],
        key="init_stock_file"
    )

# Parse uploaded file into raw dataframe
if uploaded_file is not None:
    st.markdown("""
        <style>
            div[data-testid="stFileUploader"] section { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
    from utils import make_solid_box
    st.markdown(make_solid_box(f"FILE LOADED: {uploaded_file.name}", "#FFDE59", "#0F172A"), unsafe_allow_html=True)
    if st.button("HAPUS FILE", type="secondary", use_container_width=True, icon=":material/delete:"):
        st.session_state.initial_stock_file = None
        st.session_state.initial_stock_raw = None
        st.session_state.initial_stock_df = None
        st.rerun()
    
if uploaded_file is not None and st.session_state.initial_stock_raw is None and st.session_state.initial_stock_df is None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file, dtype=str, on_bad_lines='skip')
        else:
            df_raw = pd.read_excel(uploaded_file, dtype=str)
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        st.session_state.initial_stock_raw = df_raw
        st.rerun()
    except Exception as e:
        st.error(f"Failed to parse file: {e}")

# --- COLUMN SELECTION ---
if st.session_state.initial_stock_raw is not None and st.session_state.initial_stock_df is None:
    df_raw = st.session_state.initial_stock_raw
    cols = list(df_raw.columns)

    st.subheader("Map Columns")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        # Auto-detect SKU column
        sku_default = next((i for i, c in enumerate(cols) if c.lower() in ['sku', 'kode', 'product code', 'item code', 'code']), 0)
        sel_sku = st.selectbox("SKU Column", cols, index=sku_default, key="init_sel_sku")
    with mc2:
        # Auto-detect Qty column
        qty_default = next((i for i, c in enumerate(cols) if c.lower() in ['stokakhir', 'qty', 'quantity', 'stock', 'pcs', 'stokawal', 'stok']), 0)
        sel_qty = st.selectbox("Qty Column", cols, index=qty_default, key="init_sel_qty")
    with mc3:
        # Optional description column
        desc_options = ['(None)'] + cols
        desc_default = next((i + 1 for i, c in enumerate(cols) if any(p in c.lower() for p in ['merek', 'desc', 'name', 'variant', 'nama'])), 0)
        sel_desc = st.selectbox("Description Column (optional)", desc_options, index=desc_default, key="init_sel_desc")

    # Preview raw data
    with st.expander("Preview raw data", expanded=False):
        utils.render_neo_table(df_raw.head(20))

    if st.button("Load Data", type="primary", use_container_width=True, icon=":material/upload:"):
        df_init = df_raw[[sel_sku, sel_qty]].copy()
        has_desc = sel_desc != '(None)' and sel_desc != sel_sku
        if has_desc:
            df_init[sel_desc] = df_raw[sel_desc]

        # Rename columns
        new_cols = ['SKU', 'Qty']
        if has_desc:
            new_cols.append('Description')
        df_init.columns = new_cols

        # Clean data
        df_init = df_init.dropna(subset=['SKU'])
        df_init['SKU'] = df_init['SKU'].astype(str).str.split('.').str[0].str.strip()
        df_init = df_init[~df_init['SKU'].str.lower().isin(['nan', 'none', '', 'total', 'grand total'])]
        
        # Apply SKU mapping rule
        TARGET_SKUS = database.get_target_skus(supabase)
        df_init['SKU'] = df_init['SKU'].apply(lambda x: '0' + str(x) if (str(x) in TARGET_SKUS and str(x) not in EXCLUDE_PREFIX) else x)
        df_init['Qty'] = df_init['Qty'].apply(safe_parse_numeric).astype(int)

        # Reset index
        df_init = df_init.reset_index(drop=True)

        if 'Description' not in df_init.columns:
            df_init['Description'] = ''

        st.session_state.initial_stock_df = df_init
        st.session_state.initial_stock_raw = None
        st.rerun()

# --- REVIEW UPLOADED DATA ---
if st.session_state.initial_stock_df is not None:
    df_init = st.session_state.initial_stock_df

    st.markdown(make_solid_box(f"Loaded — {len(df_init)} items from uploaded file", "#0068C9", "#0068C9"), unsafe_allow_html=True)
    if st.button("Clear Data", use_container_width=True, icon=":material/delete:"):
        st.session_state.initial_stock_df = None
        st.session_state.initial_stock_raw = None
        st.rerun()

# --- REVIEW TABLE ---
if st.session_state.initial_stock_df is not None and len(st.session_state.initial_stock_df) > 0:
    df_init = st.session_state.initial_stock_df

    # Summary metrics
    st.markdown(render_metric_card("Total SKU", len(df_init)), unsafe_allow_html=True)

    st.subheader("Initial Stock Review")

    # Warning alert if there are items with Qty <= 0
    has_invalid = (df_init['Qty'] <= 0).any()
    if has_invalid:
        st.markdown("""
            <div style='
                background-color: #F0F2F6;
                color: #31333F;
                padding: 12px 16px;
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-left: 5px solid #FF9800;
                font-size: 0.85rem;
                margin-bottom: 16px;
                font-family: "Source Sans 3", "Source Sans Pro", sans-serif;
            '>
                Warning: Terdapat SKU dengan Qty &le; 0. SKU tersebut akan ditandai sebagai 'Invalid' dan dilewati saat eksekusi agar proses tetap berhasil.
            </div>
        """, unsafe_allow_html=True)

    # Show review table
    df_display = df_init.copy()
    display_cols = ['SKU', 'Description', 'Qty'] if 'Description' in df_display.columns else ['SKU', 'Qty']
    utils.render_neo_table(df_display[display_cols])

    # --- EXECUTE ---
    if st.session_state.is_initial_running:
        st.markdown(make_solid_box("Initializing stock data...", "#0068C9", "#0068C9"), unsafe_allow_html=True)
    else:
        if st.button("Execute", type="primary", use_container_width=True, icon=":material/play_arrow:"):
            if not bot_user or not bot_pass:
                st.error("Kredensial tidak ditemukan!")
            else:
                st.session_state.is_initial_running = True
                st.rerun()

# --- PENDING EXECUTION (after rerun hides button) ---
if st.session_state.is_initial_running and st.session_state.initial_stock_df is not None:
    df_init = st.session_state.initial_stock_df

    # Build execution DataFrame (mark non-positive qty as Invalid)
    df_exec = df_init[['SKU', 'Qty']].copy()
    df_exec['Status'] = df_exec['Qty'].apply(lambda q: 'Invalid' if q <= 0 else 'Pending')
    df_exec['Keterangan'] = df_exec['Qty'].apply(lambda q: 'Invalid Qty (<= 0)' if q <= 0 else 'Ready to Input')

    st.subheader("Initial Stock Execution")
    table_placeholder = st.empty()
    utils.render_neo_table(table_placeholder, df_exec)

    log_label_placeholder = st.empty()
    log_placeholder = st.empty()

    log_label_placeholder.markdown(f"""
        <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;'>
                        <div style='background: #0068C9; color: #FFFFFF; font-family: "Source Sans 3", sans-serif; font-size: 0.85rem; font-weight: 800; padding: 6px 12px; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; text-transform: uppercase; letter-spacing: 0.05em;'>ACTIVE ACCOUNT</div>
                        <div style='background: #FFFFFF; color: #0F172A; font-family: "Source Sans 3", sans-serif; font-size: 0.85rem; font-weight: 800; padding: 6px 12px; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; text-transform: uppercase; letter-spacing: 0.05em;'>{selected_distributor} ({bot_user})</div>
                    </div>
    """, unsafe_allow_html=True)
    bot_ui_log, _ = make_terminal_logger(log_placeholder)

    playwright_engine.run_execution(
        df_exec, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE,
        REASON_CODE, TABLE_UPDATE_INTERVAL, bot_ui_log, send_telegram_alert, table_placeholder, log_label_placeholder, supabase,
        current_user=st.session_state.current_user
    )

    # Clear state after execution
    st.session_state.initial_stock_df = None

render_footer()
