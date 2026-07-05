import datetime
import time
import streamlit as st
import database
import playwright_engine
from utils import (
    make_solid_box, render_terminal, render_footer,
    check_auth, render_indicators, render_header,
    encode_param, decode_param, send_telegram_alert,
    init_session_state, make_terminal_logger, resolve_distributor_url,
)

# --- AUTH CHECK ---
check_auth()

supabase = database.init_supabase()
_sys_cfg = database.get_system_config(supabase)
URL_LOGIN  = _sys_cfg["URL_LOGIN"]
TIMEOUT_MS = _sys_cfg["TIMEOUT_MS"]

# --- STATE MANAGEMENT ---
init_session_state(is_bot_running=False)

# --- MAIN UI LAYOUT ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_bot_running else "STANDBY"

render_indicators(db_status, bot_status)
render_header("Sales Data Extraction", st.session_state.current_user)





st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True):

    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    list_dist = database.get_distributor_list(supabase)
    url_dist, default_index = resolve_distributor_url(list_dist)

    with col1:
        selected_distributor = st.selectbox("Nama Distributor", list_dist, index=default_index)
        st.query_params.clear()
        st.query_params["d"] = encode_param(selected_distributor)
        bot_user, bot_pass = database.get_distributor_creds(supabase, selected_distributor)
            
    with col2:
        from datetime import timezone, timedelta
        today_jakarta = datetime.datetime.now(timezone(timedelta(hours=7))).date()
        start_date = st.date_input("Start Date", value=today_jakarta.replace(day=1))
    
    with col3:
        # Default end date to end of current month
        next_month = start_date.replace(day=28) + datetime.timedelta(days=4)
        end_date_default = next_month - datetime.timedelta(days=next_month.day)
        end_date = st.date_input("End Date", value=end_date_default)
    
    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    if start_date > end_date:
        st.error("Start date must be before or equal to end date.")
        st.stop()
        
st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
btn_label = "Extracting…" if st.session_state.is_bot_running else "Extract Invoice"
extract_btn = st.button(btn_label, type="primary", use_container_width=True, disabled=st.session_state.is_bot_running, icon=":material/download:")
    
if st.session_state.get('sales_csv_data'):
        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        st.download_button(
            label="Download Extracted Data (ZIP)",
            data=st.session_state.sales_csv_data,
            file_name=st.session_state.sales_csv_filename,
            mime="application/zip",
            use_container_width=True
        )
 
ext_label_placeholder = st.empty()
ext_log_placeholder = st.empty()
 
# --- TRIGGER EXTRACTION ---
if extract_btn:
    if not bot_user or not bot_pass:
        st.error("Gagal! Kredensial untuk distributor ini tidak ditemukan di Supabase.")
        st.stop()
 
    st.session_state.is_bot_running = True

    ext_ui_log, _ = make_terminal_logger(ext_log_placeholder)

    # Convert dates to DD/MM/YYYY format
    start_date_str = start_date.strftime("%d/%m/%Y")
    end_date_str = end_date.strftime("%d/%m/%Y")

    playwright_engine.run_sales_extract(
        bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, 
        start_date_str, end_date_str,
        ext_ui_log, send_telegram_alert, supabase, st.session_state.current_user,
        ext_label_placeholder=ext_label_placeholder
    )

render_footer()
