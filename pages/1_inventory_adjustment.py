import time
import streamlit as st
import database
import data_processor
import pandas as pd
import playwright_engine
import importlib
importlib.reload(playwright_engine)
from utils import (
    make_solid_box, make_success_box, render_terminal, render_footer,
    check_auth, render_indicators, render_header,
    encode_param, decode_param, send_telegram_alert,
    init_session_state, render_wakelock,
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

# --- STATE MANAGEMENT & STYLING ---
init_session_state(
    reconcile_result=None,
    reconcile_summary=None,
    np_df=None,
    is_bot_running=False,
    prev_file2=None,
    current_np_user_id="",
    execute_done=False,
    adj_mode="Auto Compare",
    manual_df=pd.DataFrame([{"SKU": "", "PAC": 0, "CAR": 0, "EA": 0}]),
)

render_wakelock()

# --- MAIN UI LAYOUT ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_bot_running else "STANDBY"

render_indicators(db_status, bot_status)
render_header("Inventory Adjustment", st.session_state.current_user)

st.markdown("""
<style>
/* Styling khusus untuk stSegmentedControl (Auto Compare / Manual Entry) */
div[data-testid="stSegmentedControl"] p,
div[data-testid="stSegmentedControl"] span {
    font-family: "Source Sans 3", sans-serif !important;
    font-size: 0.65rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    font-weight: 800 !important;
    color: #31333F !important;
}

/* Selected state */
div[data-testid="stSegmentedControl"] [aria-selected="true"] p,
div[data-testid="stSegmentedControl"] [aria-selected="true"] span,
div[data-testid="stSegmentedControl"] [data-selected="true"] p,
div[data-testid="stSegmentedControl"] [data-selected="true"] span,
div[data-testid="stSegmentedControl"] input:checked + div p,
div[data-testid="stSegmentedControl"] input:checked + div span {
    font-weight: 700 !important;
    color: #0068C9 !important;
}
</style>
""", unsafe_allow_html=True)

adj_mode_sel = st.segmented_control("Adjustment Mode", ["Auto Compare", "Manual Entry"], default="Auto Compare", selection_mode="single", label_visibility="collapsed")
adj_mode = adj_mode_sel if adj_mode_sel else "Auto Compare"

if adj_mode == "Auto Compare":
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown(f"<div class='box-np'>Newspage Stock Data</div>", unsafe_allow_html=True)
            np_col1, np_col2 = st.columns(2)
        
            list_dist = database.get_distributor_list(supabase)
            url_d = st.query_params.get("d", None)
            url_dist = None
            if url_d:
                url_dist = decode_param(url_d)
            else:
                plain_dist = st.query_params.get("distributor", None)
                if plain_dist:
                    url_dist = plain_dist
                    st.query_params.pop("distributor", None)
                
            default_index = list_dist.index(url_dist) if url_dist in list_dist else 0

            with np_col1:
                selected_distributor = st.selectbox("Nama Distributor", list_dist, index=default_index)
                st.query_params.clear()
                st.query_params["d"] = encode_param(selected_distributor)
                bot_user, bot_pass = database.get_distributor_creds(supabase, selected_distributor)
                if bot_user: st.session_state.current_np_user_id = bot_user
                
            with np_col2:
                st.text_input("NP Password", value="********", type="password", disabled=True, key="np_pass_dummy")
        
            btn_label = "Step 1: Extracting..." if st.session_state.is_bot_running else "Step 1: Extract Real-time Stock from Newspage"
            extract_btn = st.button(btn_label, type="primary", width="stretch", disabled=st.session_state.is_bot_running)
            file1 = None

    with col2:
        with st.container(border=True):
            st.markdown(f"<div class='box-dist'>Distributor Stock Data</div>", unsafe_allow_html=True)
            def handle_fragment_upload():
                f = st.file_uploader("Upload Distributor stock file", type=['csv', 'xlsx'], key="file2_uploader")
                st.markdown("<div style='margin-bottom: 28px;'></div>", unsafe_allow_html=True)
                curr_f = getattr(f, "file_id", f.name if f else None) if f else None
                if curr_f != st.session_state.prev_file2:
                    st.session_state.prev_file2 = curr_f
                    if not st.session_state.is_bot_running: st.rerun()

            if hasattr(st, "fragment"):
                @st.fragment
                def render_upload_dist(): handle_fragment_upload()
                render_upload_dist()
            elif hasattr(st, "experimental_fragment"):
                @st.experimental_fragment
                def render_upload_dist(): handle_fragment_upload()
                render_upload_dist()
            else:
                handle_fragment_upload()
            file2 = st.session_state.get("file2_uploader")

    if st.session_state.np_df is not None:
        st.markdown(make_solid_box(f"Extracted — {len(st.session_state.np_df)} items loaded from server", "#0068C9", "#0068C9"), unsafe_allow_html=True)
        if st.button("Clear extracted data", width="stretch"):
            st.session_state.np_df = None
            st.rerun()

    ext_label_placeholder = st.empty()
    ext_log_placeholder = st.empty()

    # --- TRIGGER EXTRACTION ---
    if extract_btn:
        if not bot_user or not bot_pass:
            st.error("Gagal! Kredensial untuk distributor ini tidak ditemukan di Supabase.")
            st.stop()

        st.session_state.is_bot_running = True
        ext_label_placeholder.markdown(f"""
            <div style='display: inline-block; margin-bottom: 4px;'>
                <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>System Activity</span>
                <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>EXTRACT_LOG</span>
            </div>
        """, unsafe_allow_html=True)
        ext_logs_history  = []
        ext_last_log_time = [time.time()]

        def ext_ui_log(module, msg):
            now = time.time(); diff_ms = int((now - ext_last_log_time[0]) * 1000); ext_last_log_time[0] = now
            from datetime import datetime, timezone, timedelta
            timestamp = datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')
            tag_class = f"tag-{module.lower()}"
            ext_logs_history.append(f"<span class='log-time'>[{timestamp}]</span><span class='log-ms'>[+{diff_ms}ms]</span><span class='log-tag {tag_class}'>[{module}]</span><span class='log-msg'>{msg}</span>")
            render_terminal(ext_log_placeholder, ext_logs_history)

        playwright_engine.run_extract(
            bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, 
            ext_ui_log, send_telegram_alert, supabase, st.session_state.current_user
        )


    # --- DATA COMPARISON ---
    np_source_ready = (st.session_state.np_df is not None) or (file1 is not None)
    if np_source_ready and file2:
        df1 = st.session_state.np_df if st.session_state.np_df is not None else data_processor.load_data(file1)
        df2 = data_processor.load_data(file2)
    
        if df1 is None or df2 is None:
            st.error("Gagal memuat data dari file.")
            st.stop()
        
        st.markdown(f"<div class='box-results'>Results</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown(f"<div class='box-np'>Newspage Setup</div>", unsafe_allow_html=True)
                idx_sku1 = df1.columns.get_loc('Product Code') if 'Product Code' in df1.columns else 0
                if 'Product Description' in df1.columns: idx_desc1 = df1.columns.get_loc('Product Description')
                elif 'Product Name' in df1.columns: idx_desc1 = df1.columns.get_loc('Product Name')
                else: idx_desc1 = 1 if len(df1.columns) > 1 else 0
                idx_qty1 = (df1.columns.get_loc('Stock Available') if 'Stock Available' in df1.columns else (2 if len(df1.columns) > 2 else 0))
                sku_col1  = st.selectbox("SKU column (NP)", df1.columns, index=idx_sku1)
                desc_col1 = st.selectbox("Description column (NP)", df1.columns, index=idx_desc1)
                qty_col1  = st.selectbox("Qty column (NP)", df1.columns, index=idx_qty1)
        with c2:
            with st.container(border=True):
                st.markdown(f"<div class='box-dist'>Distributor Setup</div>", unsafe_allow_html=True)
                idx_sku2 = 20 if len(df2.columns) > 20 else 0
                qty2_col_match = next((col for col in df2.columns if str(col).strip().lower().replace(" ", "") == "stokakhir"), None)
                if qty2_col_match: idx_qty2 = df2.columns.get_loc(qty2_col_match)
                else: idx_qty2 = 71 if len(df2.columns) > 71 else (1 if len(df2.columns) > 1 else 0)
                sku_col2 = st.selectbox("SKU column (Dist)", df2.columns, index=idx_sku2)
                qty_col2 = st.selectbox("Qty column (Dist)", df2.columns, index=idx_qty2)
                st.markdown("<div style='margin-bottom: 84px;'></div>", unsafe_allow_html=True)

        if st.button("Step 2: Start Automated Adjustment", type="primary", width="stretch"):
            TARGET_SKUS = database.get_target_skus(supabase)
            multipliers = database.get_multiplier_rules(supabase, st.session_state.current_np_user_id)
        
            merged, mismatches = data_processor.process_compare(
                df1, df2, sku_col1, desc_col1, qty_col1, sku_col2, qty_col2, TARGET_SKUS, multipliers, st.session_state.current_np_user_id
            )
        
            if len(mismatches) == 0: 
                st.markdown(make_success_box("Analysis complete: all sku matched!"), unsafe_allow_html=True)
                st.session_state.reconcile_summary = None
            else:
                valid_mismatches = mismatches.copy()
                st.session_state.reconcile_summary = {'total_match': len(merged[merged['Selisih'] == 0]), 'total_mismatch': len(mismatches), 'df_view': mismatches[['SKU', 'Description', 'Newspage', 'Distributor', 'Selisih', 'Status']]}
                transfer_df = (valid_mismatches[['SKU', 'Selisih', 'Status']].rename(columns={'SKU': 'SKU', 'Selisih': 'Qty', 'Status': 'Status'}))
                st.session_state.reconcile_result = transfer_df
                st.rerun()


    # --- EXECUTION / INJECTION ---
    if st.session_state.reconcile_summary is not None and st.session_state.reconcile_result is not None:
        st.markdown(f"<div class='box-review'>Stock Review</div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2); match_count = st.session_state.reconcile_summary['total_match']; mismatch_count = st.session_state.reconcile_summary['total_mismatch']
        with m1: st.markdown(f'''<div class="metric-box-match"><div class="metric-label">Match</div><div class="metric-value">{match_count}</div></div>''', unsafe_allow_html=True)
        with m2: st.markdown(f'''<div class="metric-box-mismatch"><div class="metric-label">Stock difference</div><div class="metric-value">{mismatch_count}</div></div>''', unsafe_allow_html=True)
        st.dataframe(st.session_state.reconcile_summary['df_view'], width="stretch", hide_index=True, column_config={"SKU": st.column_config.TextColumn("SKU", width="medium"), "Description": st.column_config.TextColumn("Description", width="large")})
    
        df_view = st.session_state.reconcile_result.copy()
        df_view['Status'] = df_view['Status'].apply(lambda x: 'Pending' if x == 'Mismatch' else x)
        if 'Keterangan' not in df_view.columns: df_view['Keterangan'] = 'Ready to Process'
    
        st.markdown(f"<div class='box-queue'>Adjustment SKU List</div>", unsafe_allow_html=True)
        table_placeholder = st.empty(); table_placeholder.dataframe(df_view, width="stretch", hide_index=True)
    
        log_label_placeholder = st.empty()
        log_placeholder = st.empty()
        btn_placeholder = st.empty()
            
        if btn_placeholder.button("EXECUTE", type="primary", width="stretch"):
            if not bot_user or not bot_pass: 
                st.error("Access Denied: Kredensial tidak ditemukan di Database!")
            else:
                st.session_state.is_bot_running = True
                st.session_state.execute_done = False
                btn_placeholder.empty()
            
                log_label_placeholder.markdown(f"""
                    <div style='display: inline-block; margin-bottom: 4px;'>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>Active Account</span>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>{selected_distributor} ({bot_user})</span>
                    </div>
                """, unsafe_allow_html=True)
                bot_logs_history  = []; bot_last_log_time = [time.time()]
            
                def bot_ui_log(module, msg):
                    now = time.time(); diff_ms = int((now - bot_last_log_time[0]) * 1000); bot_last_log_time[0] = now
                    from datetime import datetime, timezone, timedelta
                    timestamp = datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')
                    tag_class = f"tag-{module.lower()}"
                    bot_logs_history.append(f"<span class='log-time'>[{timestamp}]</span><span class='log-ms'>[+{diff_ms}ms]</span><span class='log-tag {tag_class}'>[{module}]</span><span class='log-msg'>{msg}</span>")
                    render_terminal(log_placeholder, bot_logs_history)

                playwright_engine.run_execution(
                    df_view, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, 
                    REASON_CODE, TABLE_UPDATE_INTERVAL, bot_ui_log, send_telegram_alert, table_placeholder, log_label_placeholder, supabase
                )

elif adj_mode == "Manual Entry":
    list_dist = database.get_distributor_list(supabase)
    url_d = st.query_params.get("d", None)
    url_dist = decode_param(url_d) if url_d else st.query_params.get("distributor", None)
    default_index = list_dist.index(url_dist) if url_dist in list_dist else 0
    
    st.markdown(f"<div class='box-np'>Target Distributor Setup</div>", unsafe_allow_html=True)
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        selected_distributor = st.selectbox("Nama Distributor", list_dist, index=default_index, key="manual_dist_sel")
        st.query_params.clear()
        st.query_params["d"] = encode_param(selected_distributor)
        bot_user, bot_pass = database.get_distributor_creds(supabase, selected_distributor)
    with d_col2:
        st.text_input("NP Password", value="********", type="password", disabled=True, key="manual_pass_dummy")
        
    st.markdown(f"<br><div class='box-dist'>Manual Data Entry</div>", unsafe_allow_html=True)
    st.caption("Input SKU and its respective quantities. Rows with missing SKUs or all quantities 0 will be ignored during execution.")
    
    edited_df = st.data_editor(
        st.session_state.manual_df,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "SKU": st.column_config.TextColumn("SKU Code", required=True),
            "PAC": st.column_config.NumberColumn("Qty PAC", default=0),
            "CAR": st.column_config.NumberColumn("Qty CAR", default=0),
            "EA": st.column_config.NumberColumn("Qty EA", default=0),
        },
        key="manual_editor"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    log_label_placeholder = st.empty()
    log_placeholder = st.empty()
    btn_placeholder = st.empty()
    table_placeholder = st.empty()

    if btn_placeholder.button("EXECUTE MANUAL ADJUSTMENT", type="primary", width="stretch"):
        if not bot_user or not bot_pass: 
            st.error("Access Denied: Kredensial tidak ditemukan di Database!")
        else:
            # Clean dataframe
            df_exec = edited_df.copy()
            df_exec['SKU'] = df_exec['SKU'].astype(str).str.strip()
            for col in ['PAC', 'CAR', 'EA']:
                df_exec[col] = pd.to_numeric(df_exec[col], errors='coerce').fillna(0)
            # Filter valid rows: SKU not empty and (PAC != 0 or CAR != 0 or EA != 0)
            df_exec = df_exec[
                (df_exec['SKU'] != "") & (df_exec['SKU'] != "nan") & (df_exec['SKU'].notna()) &
                ((df_exec['PAC'] != 0) | (df_exec['CAR'] != 0) | (df_exec['EA'] != 0))
            ].copy()
            
            if len(df_exec) == 0:
                st.warning("Data kosong atau invalid. Masukkan minimal 1 SKU dengan qty tidak sama dengan 0.")
            else:
                df_exec['Status'] = 'Pending'
                df_exec['Keterangan'] = 'Ready to Process'
                df_exec = df_exec.reset_index(drop=True)
                
                table_placeholder.dataframe(df_exec, width="stretch", hide_index=True)
                st.session_state.is_bot_running = True
                st.session_state.execute_done = False
                btn_placeholder.empty()
                
                log_label_placeholder.markdown(f"""
                    <div style='display: inline-block; margin-bottom: 4px;'>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>Active Account</span>
                        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>{selected_distributor} ({bot_user})</span>
                    </div>
                """, unsafe_allow_html=True)
                bot_logs_history  = []; bot_last_log_time = [time.time()]
                
                def bot_ui_log(module, msg):
                    now = time.time(); diff_ms = int((now - bot_last_log_time[0]) * 1000); bot_last_log_time[0] = now
                    from datetime import datetime, timezone, timedelta
                    timestamp = datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')
                    tag_class = f"tag-{module.lower()}"
                    bot_logs_history.append(f"<span class='log-time'>[{timestamp}]</span><span class='log-ms'>[+{diff_ms}ms]</span><span class='log-tag {tag_class}'>[{module}]</span><span class='log-msg'>{msg}</span>")
                    render_terminal(log_placeholder, bot_logs_history)

                playwright_engine.run_execution_manual(
                    df_exec, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, 
                    REASON_CODE, TABLE_UPDATE_INTERVAL, bot_ui_log, send_telegram_alert, table_placeholder, log_label_placeholder, supabase
                )

render_footer()
