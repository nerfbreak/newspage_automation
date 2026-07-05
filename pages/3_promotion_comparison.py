# v1.3.1 - Comparison Fix & Cleanup
import datetime
import io
import time
import zipfile

import pandas as pd
import streamlit as st
import utils

import database
import playwright_engine
from utils import (
    make_solid_box, render_terminal, render_footer,
    check_auth, render_indicators, render_header,
    encode_param, decode_param, init_session_state,
    make_terminal_logger, resolve_date_url,
)

# --- AUTH CHECK ---
check_auth()

supabase = database.init_supabase()
_sys_cfg = database.get_system_config(supabase)
URL_LOGIN  = _sys_cfg["URL_LOGIN"]
TIMEOUT_MS = _sys_cfg["TIMEOUT_MS"]

# --- STATE MANAGEMENT ---
init_session_state(
    is_promo_bot_running=False,
    uploaded_mdm_data=None,
    uploaded_bdp_data=None,
    promo_zip_data=None,
    comparison_results=None,
)

# --- MAIN UI LAYOUT ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_promo_bot_running else "STANDBY"

render_indicators(db_status, bot_status, bot_type="PROMO ENGINE")
render_header("Promotion Comparison", st.session_state.current_user)





# --- FILE UPLOADER SECTION ---
st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True):

    
    uploaded_file = st.file_uploader("Drag & Drop Newspage BDP Tracker.xlsx here", type=["xlsx"])
    
    if uploaded_file:
        try:
            with st.spinner("Membaca data dari Excel..."):
                xl = pd.ExcelFile(uploaded_file)
                available_sheets = xl.sheet_names
                
                if "tracker MDM" in available_sheets:
                    st.session_state.uploaded_mdm_data = pd.read_excel(xl, sheet_name="tracker MDM")
                    from utils import make_solid_box
                    st.markdown(f"""
                        <style>
                            div[data-testid="stFileUploader"] section {{ display: none !important; }}
                            div[data-testid="stFileUploader"] {{ margin-bottom: -1rem !important; padding-bottom: 0px !important; }}
                        </style>
                        {make_solid_box(f"FILE LOADED: {uploaded_file.name}", "#FFDE59", "#0F172A")}
                    """, unsafe_allow_html=True)
                    with st.container():
                        st.markdown("<span class='red-btn-marker'></span>", unsafe_allow_html=True)
                        if st.button("Hapus File Upload", type="secondary", use_container_width=True, icon=":material/delete:"):
                            # Just force rerun to clear
                            st.rerun()
                
                if "BDP" in available_sheets:
                    st.session_state.uploaded_bdp_data = pd.read_excel(xl, sheet_name="BDP")
                    st.success("Sheet 'BDP' berhasil dibaca!")
        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- EXTRACTION CONTROLS ---
st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True):

    
    col1, col2 = st.columns([1, 1])
    
    default_sd, default_ed = resolve_date_url()

    with col1:
        start_date = st.date_input("Extraction Start Date", value=default_sd)
    with col2:
        end_date = st.date_input("Extraction End Date", value=default_ed)
        
    st.query_params.clear()
    st.query_params["sd"] = encode_param(start_date.strftime("%Y-%m-%d"))
    st.query_params["ed"] = encode_param(end_date.strftime("%Y-%m-%d"))

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    if start_date > end_date:
        st.error("Start date must be before or equal to end date.")
        st.stop()

    btn_label = "Syncing & Comparing..." if st.session_state.is_promo_bot_running else "Start Sync"
    promo_btn = st.button(btn_label, type="primary", use_container_width=True, disabled=st.session_state.is_promo_bot_running, icon=":material/sync:")

# --- TERMINAL & LOGS ---
promo_label_placeholder = st.empty()
promo_log_placeholder = st.empty()

# --- PREVIEW DATA ---
if st.session_state.uploaded_mdm_data is not None:
    @st.dialog("Preview SharePoint Data (MDM)")
    def preview_mdm_data():
        utils.render_neo_table(st.session_state.uploaded_mdm_data.head(50))

    if st.button("Preview SharePoint Data (MDM)", type="primary"):
        preview_mdm_data()

# --- TRIGGER EXTRACTION ---
if promo_btn:
    bot_user = st.secrets.get("NP_USER_SUPER")
    bot_pass = st.secrets.get("NP_PASS_SUPER")
    
    if not bot_user or not bot_pass:
        st.error("Kredensial SUPERUSER tidak ditemukan di secrets.toml!")
        st.stop()

    st.session_state.is_promo_bot_running = True

    promo_ui_log, _ = make_terminal_logger(promo_log_placeholder)

    sd_str = start_date.strftime("%d/%m/%Y")
    ed_str = end_date.strftime("%d/%m/%Y")

    def alert_dummy(msg): pass

    try:
        playwright_engine.run_promotion_sync(
            bot_user, bot_pass, "GLOBAL", URL_LOGIN,
            TIMEOUT_MS, sd_str, ed_str, promo_ui_log, alert_dummy, supabase, st.session_state.current_user
        )
    except Exception as e:
        promo_ui_log("ERROR", f"Extraction failed: {str(e)}")
    
    st.session_state.is_promo_bot_running = False
    st.rerun()

# --- COMPARISON VIEW ---
if st.session_state.promo_zip_data:
    st.markdown("---")
    st.markdown("<h3>Smart Comparison Engine</h3>", unsafe_allow_html=True)
    
    if st.session_state.uploaded_mdm_data is None:
        st.warning("Mohon upload file Excel SharePoint di atas untuk mulai membandingkan.")
        st.stop()
        
    st.success("Data Newspage & Excel SharePoint siap dibandingkan!")
    
    if st.button("Run Analysis", type="primary", use_container_width=True, icon=":material/play_arrow:"):
        with st.spinner("Menganalisis kecocokan data..."):
            try:
                # 1. Process Newspage ZIP
                all_np_rows = []
                with zipfile.ZipFile(io.BytesIO(st.session_state.promo_zip_data)) as z:
                    for filename in z.namelist():
                        if filename.endswith('.csv'):
                            with z.open(filename) as f:
                                df_temp = pd.read_csv(f, sep='|', encoding='utf-8')
                                all_np_rows.append(df_temp)
                
                if not all_np_rows:
                    st.error("Tidak ditemukan data CSV di dalam ZIP hasil ekstraksi.")
                    st.stop()
                    
                df_np_total = pd.concat(all_np_rows, ignore_index=True)
                df_np_total.columns = [c.strip().upper() for c in df_np_total.columns]
                
                # 3. Preparation for Comparison
                df_sp = st.session_state.uploaded_mdm_data.copy()
                
                # Normalize Column Names for Robustness
                sp_code_col = 'Promo Code (20)' if 'Promo Code (20)' in df_sp.columns else df_sp.columns[0]
                np_code_col = 'PROMO_CODE' if 'PROMO_CODE' in df_np_total.columns else df_np_total.columns[0]
                
                df_sp[sp_code_col] = df_sp[sp_code_col].astype(str).str.strip().str.upper()
                df_np_total[np_code_col] = df_np_total[np_code_col].astype(str).str.strip().str.upper()
                
                # 4. Perform Merge
                df_merge = pd.merge(
                    df_sp, 
                    df_np_total, 
                    left_on=sp_code_col, 
                    right_on=np_code_col, 
                    how='left',
                    suffixes=('_SP', '_NP')
                )
                
                # 5. Smart Validation Logic
                def validate_promo(row):
                    if pd.isnull(row[np_code_col]):
                        return "MISSING", "Promo not found in Newspage"
                    
                    issues = []
                    
                    # Date Validation (Attempt to normalize)
                    try:
                        # SP Dates
                        sp_start = pd.to_datetime(row.get('Start Date', None))
                        sp_end = pd.to_datetime(row.get('End Date', None))
                        
                        # NP Dates
                        np_start = pd.to_datetime(row.get('START_DATE', None))
                        np_end = pd.to_datetime(row.get('END_DATE', None))
                        
                        if pd.notnull(sp_start) and pd.notnull(np_start):
                            if sp_start.date() != np_start.date():
                                issues.append(f"Start Date Mismatch ({sp_start.date()} vs {np_start.date()})")
                        
                        if pd.notnull(sp_end) and pd.notnull(np_end):
                            if sp_end.date() != np_end.date():
                                issues.append(f"End Date Mismatch ({sp_end.date()} vs {np_end.date()})")
                    except:
                        pass # Skip if date parsing fails

                    # Status Validation
                    sp_status = str(row.get('Promo Status', '')).strip().upper()
                    np_status = str(row.get('STATUS', '')).strip().upper()
                    if sp_status and np_status:
                        # Map statuses if needed (e.g. 'ACTIVE' vs 'A')
                        if sp_status[0] != np_status[0]: # Simple first-letter match as heuristic
                            issues.append(f"Status Conflict ({sp_status} vs {np_status})")

                    if not issues:
                        return "MATCH", "All good"
                    else:
                        return "CONFLICT", " | ".join(issues)

                # Apply Validation
                results = df_merge.apply(validate_promo, axis=1, result_type='expand')
                df_merge['MATCH_STATUS'] = results[0]
                df_merge['ISSUE_DETAILS'] = results[1]
                
                st.session_state.comparison_results = df_merge
                match_count = len(df_merge[df_merge['MATCH_STATUS'] == 'MATCH'])
                conflict_count = len(df_merge[df_merge['MATCH_STATUS'] == 'CONFLICT'])
                st.success(f"Analisis Selesai! {match_count} Match, {conflict_count} Conflict ditemukan.")
            except Exception as e:
                st.error(f"Error during comparison: {e}")

    # Display Results
    if st.session_state.comparison_results is not None:
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        filter_status = st.radio("Filter Results", ["All", "MATCH", "CONFLICT", "MISSING"], horizontal=True)
        
        df_view = st.session_state.comparison_results
        if filter_status != "All":
            df_view = df_view[df_view['MATCH_STATUS'] == filter_status]
            
        utils.render_neo_table(df_view)
        
        csv_buffer = io.StringIO()
        df_view.to_csv(csv_buffer, index=False)
        from datetime import datetime, timezone, timedelta
        st.download_button(
            label="Download Comparison Result (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"promo_comparison_{datetime.now(timezone(timedelta(hours=7))).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch"
        )

    st.download_button(
        label="Download Raw Newspage Data (ZIP)",
        data=st.session_state.promo_zip_data,
        file_name="newspage_promo_extraction.zip",
        mime="application/zip",
        width="stretch"
    )

render_footer()
