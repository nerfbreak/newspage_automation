import time
import html as _html
import streamlit as st
import database
from utils import (
    render_footer, inject_css, send_telegram_alert,
    init_session_state, render_wakelock,
)

# --- 1. CONFIG & UI HELPERS ---
st.set_page_config(page_title="Stock Adjustment Newspage", layout="wide")
inject_css()
supabase = database.init_supabase()
# Pre-warm the config cache so pages can access it without re-querying
_config = database.get_system_config(supabase)

# --- 2. AUTHENTICATION GATEKEEPER ---
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour

init_session_state(
    logged_in=False,
    current_user="unknown",
    login_attempts=0,
    lockout_until=0,
    last_activity=0,
)

# --- SESSION TIMEOUT ---
if st.session_state.logged_in and st.session_state.last_activity > 0:
    idle = time.time() - st.session_state.last_activity
    if idle > SESSION_TIMEOUT_SECONDS:
        st.session_state.logged_in = False
        st.session_state.current_user = "unknown"
        st.session_state.login_attempts = 0
        st.toast("Session expired. Please sign in again.")
        st.rerun()
    else:
        st.session_state.last_activity = time.time()

if not st.session_state.logged_in:
    inject_css("login.css")

    with st.form("login_form"):
        st.markdown("<div style='text-align: center;'><h4 style='color: #31333F; font-weight: 500; margin-bottom: 24px; font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Helvetica, Arial, sans-serif;'>Sign in</h4></div>", unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="")
        password = st.text_input("Password", type="password", placeholder="")
        
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        # Check lockout
        is_locked = time.time() < st.session_state.lockout_until
        if is_locked:
            remaining = int(st.session_state.lockout_until - time.time())
            st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Too many failed attempts. Locked for {remaining}s.</p>", unsafe_allow_html=True)
        
        submit = st.form_submit_button("LOGIN", type="primary", width="stretch", disabled=is_locked)
        
        if submit and not is_locked:
            if database.authenticate_user(supabase, username, password):
                with st.spinner("Authenticating..."):
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.login_attempts = 0
                    st.session_state.lockout_until = 0
                    st.session_state.last_activity = time.time()
                    st.toast("Authentication Successful. Welcome Back.")
                    time.sleep(1.2)
                    st.rerun()
            else:
                st.session_state.login_attempts += 1
                attempts_left = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts
                if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
                    st.session_state.lockout_until = time.time() + LOCKOUT_SECONDS
                    send_telegram_alert(f"[ALERT] Account lockout triggered for user: <b>{_html.escape(username)}</b>\n{MAX_LOGIN_ATTEMPTS} failed attempts.")
                    st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Account locked for {LOCKOUT_SECONDS // 60} minutes due to too many failed attempts.</p>", unsafe_allow_html=True)
                else:
                    time.sleep(1.5)  # Slow down brute-force attempts
                    st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Invalid credentials. {attempts_left} attempt(s) remaining.</p>", unsafe_allow_html=True)

    render_footer()
    st.stop()

# --- 3. STATE MANAGEMENT & STYLING ---
init_session_state(
    reconcile_result=None,
    reconcile_summary=None,
    np_df=None,
    is_bot_running=False,
    prev_file2=None,
    current_np_user_id="",
    execute_done=False,
)

render_wakelock()


# Define pages
dashboard_page = st.Page("pages/0_dashboard.py", title="Dashboard", url_path="dashboard", default=True)
inventory_page = st.Page("pages/1_inventory_adjustment.py", title="Inventory Adjustment", url_path="p1")
sales_page = st.Page("pages/2_sales_extraction.py", title="Sales Extraction", url_path="p2")
promotion_page = st.Page("pages/3_promotion_comparison.py", title="Promotion Comparison", url_path="p3")
mutation_page = st.Page("pages/4_stock_mutation.py", title="Stock Mutation", url_path="p4")
clearance_page = st.Page("pages/5_clearance_stock.py", title="Clearance Stock", url_path="p5")
initial_page = st.Page("pages/6_initial_stock.py", title="Initial Stock", url_path="p6")

# Run navigation
pg = st.navigation([dashboard_page, inventory_page, sales_page, promotion_page, mutation_page, clearance_page, initial_page], position="hidden")
pg.run()

