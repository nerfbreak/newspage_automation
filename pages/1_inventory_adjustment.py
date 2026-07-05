import time
import io
import os
import streamlit as st
import utils
import database
import data_processor
import pandas as pd
import playwright_engine
from utils import (
    make_solid_box, make_success_box, render_terminal, render_footer,
    check_auth, render_indicators, render_header,
    encode_param, decode_param, send_telegram_alert,
    init_session_state, render_wakelock, make_terminal_logger, resolve_distributor_url,
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
    manual_uploader_key=0,
    manual_uploaded_df=None,
)

render_wakelock()

# --- MAIN UI LAYOUT ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_bot_running else "STANDBY"

render_indicators(db_status, bot_status)
render_header("Inventory Adjustment", st.session_state.current_user)





adj_mode_sel = st.segmented_control("Adjustment Mode", ["Auto Compare", "Manual Entry"], default="Auto Compare", selection_mode="single", label_visibility="collapsed")
adj_mode = adj_mode_sel if adj_mode_sel else "Auto Compare"

if "Auto Compare" in adj_mode:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
        with st.container(border=True):
            list_dist = database.get_distributor_list(supabase)
            url_dist, default_index = resolve_distributor_url(list_dist)

            selected_distributor = st.selectbox("Nama Distributor", list_dist, index=default_index)
            st.query_params.clear()
            st.query_params["d"] = encode_param(selected_distributor)
            bot_user, bot_pass = database.get_distributor_creds(supabase, selected_distributor)
            if bot_user: st.session_state.current_np_user_id = bot_user
            file1 = None
            
    # extract_btn moved below columns
    with col2:
        st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
        with st.container(border=True):
            def handle_fragment_upload():
                if "f2_key" not in st.session_state: st.session_state.f2_key = 0
                f = st.file_uploader("Upload Distributor stock file", type=['csv', 'xlsx'], key=f"file2_uploader_{st.session_state.f2_key}")
                if f:
                    from utils import make_solid_box
                    st.markdown(f"""
                        <style>
                            div[data-testid="stFileUploader"] section {{ display: none !important; }}
                            div[data-testid="stFileUploader"] {{ margin-bottom: -1rem !important; padding-bottom: 0px !important; }}
                        </style>
                        {make_solid_box(f"FILE LOADED: {f.name}", "#FFDE59", "#0F172A")}
                    """, unsafe_allow_html=True)
                    with st.container():
                        st.markdown("<span class='red-btn-marker'></span>", unsafe_allow_html=True)
                        if st.button("Hapus File Upload Stock Distributor", type="secondary", width='stretch', icon=":material/delete:"):
                            st.session_state.f2_key += 1
                            st.rerun()
                else:
                    st.markdown("<div style='margin-bottom: 0px;'></div>", unsafe_allow_html=True)
                
                curr_f = getattr(f, "file_id", f.name if f else None) if f else None
                if curr_f != st.session_state.prev_file2:
                    st.session_state.prev_file2 = curr_f
                    st.session_state.show_comparison = False
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
            file2 = st.session_state.get(f"file2_uploader_{st.session_state.get('f2_key', 0)}")
            
    # --- ACTION BUTTONS ---
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    extract_btn = False
    
    if st.session_state.np_df is not None:
        with st.container():
            st.markdown("<span class='red-btn-marker'></span>", unsafe_allow_html=True)
            if st.button("Clear Data Extracted Inventory Master", type="primary", width='stretch', icon=":material/delete:"):
                st.session_state.np_df = None
                st.rerun()
    else:
        btn_label = "Extracting..." if st.session_state.is_bot_running else "Extract Stock"
        extract_btn = st.button(btn_label, type="primary", width='stretch', disabled=st.session_state.is_bot_running, icon=":material/download:")

    if st.session_state.np_df is not None:
        st.markdown(make_solid_box(f"Extracted — {len(st.session_state.np_df)} items loaded from server", "#0068C9", "#0068C9"), unsafe_allow_html=True)

    ext_label_placeholder = st.empty()
    ext_log_placeholder = st.empty()

    # --- TRIGGER EXTRACTION ---
    if extract_btn:
        if not bot_user or not bot_pass:
            st.error("Gagal! Kredensial untuk distributor ini tidak ditemukan di Supabase.")
            st.stop()

        st.session_state.is_bot_running = True
        ext_label_placeholder.markdown(f"""
            <div style='display: inline-flex; border: 2px solid #0F172A; box-shadow: 2px 2px 0px 0px #0F172A; margin-bottom: 8px; background-color: #FFFFFF; align-items: center;'>
            <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.7rem; font-weight: 900; color: #FFFFFF; background-color: #0068C9; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 8px; border-right: 2px solid #0F172A;'>System Activity</span>
            <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.7rem; font-weight: 900; color: #0F172A; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 8px;'>EXTRACT_LOG</span>
        </div>
        """, unsafe_allow_html=True)
        ext_ui_log, _ = make_terminal_logger(ext_log_placeholder)

        playwright_engine.run_extract(
            bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, 
            ext_ui_log, send_telegram_alert, supabase, st.session_state.current_user,
            ext_label_placeholder=ext_label_placeholder
        )


    # --- DATA COMPARISON ---
    np_source_ready = (st.session_state.np_df is not None) or (file1 is not None)
    
    if np_source_ready and file2:
        st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
        if st.button("PROSES FILE & BANDINGKAN", type="primary", width='stretch', icon=":material/compare_arrows:"):
            st.session_state.show_comparison = True
            
    if st.session_state.get('show_comparison') and np_source_ready and file2:
        df1 = st.session_state.np_df if st.session_state.np_df is not None else data_processor.load_data(file1)
        df2 = data_processor.load_data(file2)
    
        if df1 is None or df2 is None:
            st.error("Gagal memuat data dari file.")
            st.stop()
        
        st.markdown("<div class='header-wrapper-center'><span class='section-header-underline'>RESULTS</span></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
            with st.container(border=True, height=420):
                st.markdown("<div class='header-wrapper-left'><span class='section-header-underline'>NEWSPAGE SETUP</span></div>", unsafe_allow_html=True)
                idx_sku1 = df1.columns.get_loc('Product Code') if 'Product Code' in df1.columns else 0
                if 'Product Description' in df1.columns: idx_desc1 = df1.columns.get_loc('Product Description')
                elif 'Product Name' in df1.columns: idx_desc1 = df1.columns.get_loc('Product Name')
                else: idx_desc1 = 1 if len(df1.columns) > 1 else 0
                idx_qty1 = (df1.columns.get_loc('Stock Available') if 'Stock Available' in df1.columns else (2 if len(df1.columns) > 2 else 0))
                sku_col1  = st.selectbox("SKU column (NP)", df1.columns, index=idx_sku1)
                desc_col1 = st.selectbox("Description column (NP)", df1.columns, index=idx_desc1)
                qty_col1  = st.selectbox("Qty column (NP)", df1.columns, index=idx_qty1)
        with c2:
            st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
            with st.container(border=True, height=420):
                st.markdown("<div class='header-wrapper-left'><span class='section-header-underline'>DISTRIBUTOR SETUP</span></div>", unsafe_allow_html=True)
                idx_sku2 = 20 if len(df2.columns) > 20 else 0
                qty2_col_match = next((col for col in df2.columns if str(col).strip().lower().replace(" ", "") == "stokakhir"), None)
                if qty2_col_match: idx_qty2 = df2.columns.get_loc(qty2_col_match)
                else: idx_qty2 = 71 if len(df2.columns) > 71 else (1 if len(df2.columns) > 1 else 0)
                sku_col2 = st.selectbox("SKU column (Dist)", df2.columns, index=idx_sku2)
                qty_col2 = st.selectbox("Qty column (Dist)", df2.columns, index=idx_qty2)

        if st.button("Start Adjustment", type="primary", width='stretch', icon=":material/play_arrow:"):
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
        st.markdown("<div class='header-wrapper-center'><span class='section-header-underline'>STOCK REVIEW</span></div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2); match_count = st.session_state.reconcile_summary['total_match']; mismatch_count = st.session_state.reconcile_summary['total_mismatch']
        with m1: st.markdown(f'''<div class="metric-box-match"><div class="metric-label">Match</div><div class="metric-value">{match_count}</div></div>''', unsafe_allow_html=True)
        with m2: st.markdown(f'''<div class="metric-box-mismatch"><div class="metric-label">Stock difference</div><div class="metric-value">{mismatch_count}</div></div>''', unsafe_allow_html=True)
        utils.render_neo_table(st.session_state.reconcile_summary['df_view'])
    
        df_view = st.session_state.reconcile_result.copy()
        df_view['Status'] = df_view['Status'].apply(lambda x: 'Pending' if x == 'Mismatch' else x)
        if 'Keterangan' not in df_view.columns: df_view['Keterangan'] = 'Ready to Process'
    
        st.markdown("<div class='header-wrapper-center'><span class='section-header-underline'>ADJUSTMENT SKU LIST</span></div>", unsafe_allow_html=True)
        table_placeholder = st.empty(); utils.render_neo_table(table_placeholder, df_view)
    
        auto_remark = ""
        if file2 is not None and hasattr(file2, 'name'):
            import os
            auto_remark, _ = os.path.splitext(file2.name)
            
        remark_text = st.text_input("Remark", value=auto_remark, max_chars=50, key="auto_remark")
        
        log_label_placeholder = st.empty()
        log_placeholder = st.empty()
        btn_placeholder = st.empty()
            
        if btn_placeholder.button("EXECUTE", type="primary", width="stretch", icon=":material/play_arrow:"):
            if not remark_text.strip():
                st.warning("Kolom 'Remark' wajib diisi sebelum eksekusi.")
            elif not bot_user or not bot_pass: 
                st.error("Access Denied: Kredensial tidak ditemukan di Database!")
            else:
                st.session_state.is_bot_running = True
                st.session_state.execute_done = False
                btn_placeholder.empty()
            

                bot_ui_log, _ = make_terminal_logger(log_placeholder)
                fn = file2.name if 'file2' in locals() and file2 else None
                playwright_engine.run_execution(
                    df_view, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, 
                    REASON_CODE, TABLE_UPDATE_INTERVAL, bot_ui_log, send_telegram_alert, table_placeholder, log_label_placeholder, supabase,
                    current_user=st.session_state.current_user, remark_text=remark_text, file_name=fn
                )

elif "Manual Entry" in adj_mode:
    list_dist = database.get_distributor_list(supabase)
    url_dist, default_index = resolve_distributor_url(list_dist)
    
    st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
    with st.container(border=True):
        selected_distributor = st.selectbox("Nama Distributor", list_dist, index=default_index, key="manual_dist_sel")
        st.query_params.clear()
        st.query_params["d"] = encode_param(selected_distributor)
        bot_user, bot_pass = database.get_distributor_creds(supabase, selected_distributor)
        
    st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<div class='header-wrapper-left'><span class='section-header-underline'>OPTIONAL: UPLOAD FILE</span></div>", unsafe_allow_html=True)
        
        uploaded_manual = st.file_uploader("Upload Excel / CSV", type=["csv", "xlsx", "xls"], key=f"manual_uploader_{st.session_state.manual_uploader_key}")
        
        if uploaded_manual:
            st.markdown(make_solid_box(f"FILE LOADED: {uploaded_manual.name}", "#FFDE59", "#0F172A"), unsafe_allow_html=True)
            try:
                if uploaded_manual.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_manual)
                else:
                    df_up = pd.read_excel(uploaded_manual)
                
                st.session_state.manual_uploaded_df = df_up
            except Exception as e:
                st.error(f"Error parsing file: {e}")
                st.session_state.manual_uploaded_df = None
                
            with st.container():
                st.markdown("<span class='red-btn-marker'></span>", unsafe_allow_html=True)
                if st.button("Hapus File Upload Stock Distributor", type="secondary", icon=":material/delete:", width='stretch'):
                    st.session_state.manual_uploader_key += 1
                    st.session_state.manual_uploaded_df = None
                    st.rerun()

        if st.session_state.get("manual_uploaded_df") is not None:
            df_up = st.session_state.manual_uploaded_df
            st.dataframe(df_up.head(5), width='stretch')
            
            st.markdown("<div style='margin-bottom:10px;'><b>Mapping Kolom:</b></div>", unsafe_allow_html=True)
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            cols = ["-"] + list(df_up.columns)
            with mcol1:
                sel_sku = st.selectbox("SKU Column", cols, index=1 if len(cols)>1 else 0)
            with mcol2:
                sel_pac = st.selectbox("PAC Column", cols, index=0)
            with mcol3:
                sel_car = st.selectbox("CAR Column", cols, index=0)
            with mcol4:
                sel_ea  = st.selectbox("EA Column", cols, index=0)
                
            if st.button("Apply Mapping ke Tabel", type="primary", width='stretch', icon=":material/done_all:"):
                if sel_sku == "-":
                    st.error("SKU Column harus dipilih.")
                else:
                    new_df = pd.DataFrame()
                    new_df["SKU"] = df_up[sel_sku].astype(str)
                    new_df["PAC"] = pd.to_numeric(df_up[sel_pac], errors='coerce').fillna(0) if sel_pac != "-" else 0
                    new_df["CAR"] = pd.to_numeric(df_up[sel_car], errors='coerce').fillna(0) if sel_car != "-" else 0
                    new_df["EA"]  = pd.to_numeric(df_up[sel_ea], errors='coerce').fillna(0)  if sel_ea != "-" else 0
                    
                    st.session_state.manual_df = new_df
                    st.rerun()

    st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<div class='header-wrapper-center-notop'><span class='section-header-underline'>FIELD SKU INPUT</span></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background-color: #FFFFFF; color: #0F172A; padding: 12px 16px; border-radius: 0px; font-size: 0.75rem; font-weight: 700; border: 3px solid #0F172A; margin-bottom: 24px; box-shadow: 6px 6px 0px 0px #0F172A; display: flex; align-items: center; gap: 12px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            <span style="text-transform: uppercase;">Input SKU and its respective quantities. Rows with missing SKUs or all quantities 0 will be ignored during execution.</span>
        </div>
        """, unsafe_allow_html=True)
        
        edited_df = st.data_editor(
            st.session_state.manual_df,
            num_rows="dynamic",
            width="stretch",
            column_config={
                "SKU": st.column_config.TextColumn("SKU Code", required=True),
                "PAC": st.column_config.NumberColumn("PAC", default=0),
                "CAR": st.column_config.NumberColumn("CAR", default=0),
                "EA": st.column_config.NumberColumn("EA", default=0),
            },
            key="manual_editor"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    
    table_placeholder = st.empty()

    manual_auto_remark = ""
    if uploaded_manual is not None and hasattr(uploaded_manual, 'name'):
        import os
        manual_auto_remark, _ = os.path.splitext(uploaded_manual.name)
        
    manual_remark_text = st.text_input("Remark", value=manual_auto_remark, max_chars=50, key="manual_remark")
    
    log_label_placeholder = st.empty()
    log_placeholder = st.empty()
    btn_placeholder = st.empty()

    if btn_placeholder.button("EXECUTE MANUAL ADJUSTMENT", type="primary", width="stretch", icon=":material/play_arrow:"):
        if not manual_remark_text.strip():
            st.warning("Kolom 'Remark' wajib diisi sebelum eksekusi.")
        elif not bot_user or not bot_pass: 
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
                
                utils.render_neo_table(table_placeholder, df_exec)
                st.session_state.is_bot_running = True
                st.session_state.execute_done = False
                btn_placeholder.empty()
                

                bot_ui_log, _ = make_terminal_logger(log_placeholder)

                fn_manual = uploaded_manual.name if 'uploaded_manual' in locals() and uploaded_manual else None
                playwright_engine.run_execution_manual(
                    df_exec, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, WAREHOUSE, 
                    REASON_CODE, TABLE_UPDATE_INTERVAL, bot_ui_log, send_telegram_alert, table_placeholder, log_label_placeholder, supabase,
                    remark_text=manual_remark_text, current_user=st.session_state.current_user, file_name=fn_manual
                )

if st.session_state.get("execute_done") and st.session_state.get("last_success_shot"):
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    screenshot_path = st.session_state.last_success_shot
    
    with st.expander("BUKTI TRANSAKSI (SCREENSHOT)", expanded=False):
        st.markdown("""
        <div style="background-color: #dbeafe; color: #1e3a8a; padding: 12px 16px; border-radius: 0px; font-size: 0.85rem; font-weight: 700; border: 3px solid #0F172A; margin-bottom: 24px; box-shadow: 6px 6px 0px 0px #0F172A; display: flex; align-items: center; gap: 12px; margin-top: 12px;">
            <span style="font-size: 1.2rem;">ℹ</span>
<span>Pekerjaan selesai! Klik tombol "Kirim ke WhatsApp" di bawah untuk menyalin bukti transaksi dan membukanya di browser Anda.</span>
        </div>
        """, unsafe_allow_html=True)
        
        if os.path.exists(screenshot_path):
            import base64
            with open(screenshot_path, "rb") as file:
                img_bytes = file.read()
                b64_data = base64.b64encode(img_bytes).decode("utf-8")
            
            import streamlit.components.v1 as components
            
            import re
            
            # Convert HTML tags from telegram message to WhatsApp markdown
            js_msg = ""
            if st.session_state.get("last_alert_msg"):
                plain_msg = re.sub(r'<b>(.*?)</b>', r'*\1*', st.session_state.last_alert_msg)
                plain_msg = re.sub(r'<[^>]+>', '', plain_msg)
                # Escape for Javascript injection
                js_msg = plain_msg.replace('\n', '\\n').replace('"', '\\"').replace("'", "\\'")
            
            button_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
              body {{
                margin: 0;
                padding: 4px 10px 10px 4px;
                display: flex;
                gap: 16px;
                overflow: hidden;
                font-family: 'Source Sans 3', sans-serif, monospace;
              }}
              .neo-btn {{
                flex: 1;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                height: 42px;
                background-color: #0068C9;
                color: #FFFFFF;
                border: 2px solid #0F172A;
                border-radius: 0px;
                font-weight: 600;
                font-size: 14px;
                text-transform: uppercase;
                text-decoration: none;
                box-shadow: 6px 6px 0px 0px #0F172A;
                cursor: pointer;
                transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
                box-sizing: border-box;
              }}
              .neo-btn:hover {{
                transform: translate(2px, 2px);
                box-shadow: 4px 4px 0px 0px #0F172A;
              }}
              .neo-btn:active {{
                transform: translate(4px, 4px);
                box-shadow: 2px 2px 0px 0px #0F172A;
              }}
              svg {{
                margin-right: 8px;
              }}
            </style>
            <script>
            let preloadedBlobItem = null;

            async function preloadImage() {{
                try {{
                    const res = await fetch("data:image/png;base64,{b64_data}");
                    const blob = await res.blob();
                    
                    const clipboardData = {{
                        "image/png": blob
                    }};
                    
                    const textContent = "{js_msg}";
                    if (textContent) {{
                        clipboardData["text/plain"] = new Blob([textContent], {{ type: "text/plain" }});
                    }}
                    
                    preloadedBlobItem = new ClipboardItem(clipboardData);
                }} catch (e) {{
                    console.error("Preload failed", e);
                }}
            }}
            window.addEventListener("DOMContentLoaded", preloadImage);

            function handleCopyClick(event) {{
                const btn = event.currentTarget;
                const originalText = btn.innerHTML;
                
                if (preloadedBlobItem) {{
                    navigator.clipboard.write([preloadedBlobItem]).then(() => {{
                        btn.innerHTML = '✔ DISALIN!';
                        btn.style.backgroundColor = '#10B981';
                        setTimeout(() => {{
                            btn.innerHTML = originalText;
                            btn.style.backgroundColor = '#0068C9';
                        }}, 2000);
                    }}).catch(err => {{
                        console.error("Clipboard write failed:", err);
                        alert("Gagal menyalin, pastikan browser Anda mendukung Clipboard API.");
                    }});
                }} else {{
                    alert("Gambar belum siap, tunggu sebentar lalu coba lagi.");
                }}
            }}
            </script>
            </head>
            <body>
              <a href="data:image/png;base64,{b64_data}" download="{os.path.basename(screenshot_path)}" class="neo-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                  <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                </svg>
                UNDUH SCREENSHOT
              </a>
              <button class="neo-btn" onclick="handleCopyClick(event)">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                  <path stroke-linecap="square" stroke-linejoin="miter" d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                  <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
                </svg>
                COPY GAMBAR & TEKS
              </button>
            </body>
            </html>
            """
            
            components.html(button_html, height=60)
            st.image(screenshot_path, width='stretch')
            st.markdown("<p style='text-align: center; font-weight: 800; font-family: \"Source Sans 3\", sans-serif; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.85rem; color: #0F172A; margin-top: 8px;'>BUKTI TRANSAKSI</p>", unsafe_allow_html=True)
        else:
            st.error(f"Screenshot tidak ditemukan di {screenshot_path}.")

render_footer()
