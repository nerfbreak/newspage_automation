import time
import html as _html
import streamlit as st
import database
from utils import (
    render_footer, inject_css, send_telegram_alert,
    init_session_state, render_wakelock,
)

# --- 1. CONFIG & UI HELPERS ---
st.set_page_config(page_title="Stock Adjustment Newspage", layout="wide", page_icon="static/favicon.png")
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
        
        submit = st.form_submit_button("LOGIN", type="primary", width="stretch")
        
        if submit:
            if not username:
                st.error("Please enter a username.")
            else:
                is_locked, remaining, attempts = database.check_login_lockout(supabase, username)
                
                if is_locked:
                    st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Account locked. Please try again in {remaining} seconds.</p>", unsafe_allow_html=True)
                else:
                    if database.authenticate_user(supabase, username, password):
                        database.reset_failed_login(supabase, username)
                        st.markdown("<p style='color: #0068C9; font-size: 0.8rem; text-align: center; margin-top: 10px; font-weight: 600;'>Authentication Successful. Welcome Back.</p>", unsafe_allow_html=True)
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.session_state.last_activity = time.time()
                        time.sleep(1.2)
                        st.rerun()
                    else:
                        database.record_failed_login(supabase, username, max_attempts=MAX_LOGIN_ATTEMPTS, lockout_minutes=LOCKOUT_SECONDS // 60)
                        _, _, new_attempts = database.check_login_lockout(supabase, username)
                        attempts_left = max(0, MAX_LOGIN_ATTEMPTS - new_attempts)
                        
                        if new_attempts >= MAX_LOGIN_ATTEMPTS:
                            send_telegram_alert(f"[ALERT] Account lockout triggered for user: <b>{_html.escape(username)}</b>\n{MAX_LOGIN_ATTEMPTS} failed attempts.")
                            st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Account locked for {LOCKOUT_SECONDS // 60} minutes due to too many failed attempts.</p>", unsafe_allow_html=True)
                        else:
                            time.sleep(1.5)  # Slow down brute-force attempts
                            st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Invalid credentials. {attempts_left} attempt(s) remaining.</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("✨ What's New & Changelog", expanded=False):
        try:
            with open("CHANGELOG.md", "r", encoding="utf-8") as f:
                lines = f.readlines()
            start_idx = 0
            for idx, line in enumerate(lines):
                if line.strip().startswith("##"):
                    start_idx = idx
                    break
            changelog_content = "".join(lines[start_idx:])
            st.markdown(changelog_content)
        except Exception:
            st.markdown("""
            **v1.2.0**
            - Added Stock Mutation module.
            - Added Clearance Stock module.
            - Streamlined UI: removed unused NP Password fields.
            - Modernized session status indicator.
            """)

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

