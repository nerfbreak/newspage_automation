import datetime
import time
import streamlit as st
import database
import playwright_engine
import importlib
importlib.reload(playwright_engine)
from utils import (
    make_solid_box, render_terminal, render_footer,
    check_auth, render_indicators, render_header,
    encode_param, decode_param, send_telegram_alert,
    init_session_state,
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


with st.container(border=True):
    st.markdown(f"<div class='box-np'>Sales Extraction Setup</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
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
    btn_label = "Extracting…" if st.session_state.is_bot_running else "Extract Invoice Details"
    extract_btn = st.button(btn_label, type="primary", width='stretch', disabled=st.session_state.is_bot_running)
    
    if st.session_state.get('sales_csv_data'):
        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        st.download_button(
            label="Download Data Sales CSV",
            data=st.session_state.sales_csv_data,
            file_name=st.session_state.sales_csv_filename,
            mime="text/csv",
            width="stretch"
        )
 
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

    # Convert dates to DD/MM/YYYY format
    start_date_str = start_date.strftime("%d/%m/%Y")
    end_date_str = end_date.strftime("%d/%m/%Y")

    playwright_engine.run_sales_extract(
        bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, 
        start_date_str, end_date_str,
        ext_ui_log, send_telegram_alert, supabase, st.session_state.current_user
    )

render_footer()
