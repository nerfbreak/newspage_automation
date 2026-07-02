import os
import time
import html as _html
import streamlit as st
import extra_streamlit_components as stx
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

cookie_manager = stx.CookieManager(key="cookie_manager")
cookies = cookie_manager.get_all()
# Let the cookie manager initialize
# It needs a run to fetch cookies from the client
if cookies is None:
    st.stop()

# --- HANDLE LOGOUT ---
if st.session_state.get("logout_requested"):
    if "auth_user" in cookies:
        cookie_manager.delete("auth_user")
        cookies.pop("auth_user", None)
    st.session_state.logout_requested = False

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes
SESSION_TIMEOUT_SECONDS = 86400 * 7  # 7 days

init_session_state(
    logged_in=False,
    current_user="unknown",
    login_attempts=0,
    lockout_until=0,
    last_activity=0,
    logout_requested=False,
    ignore_cookie=False,
)

# --- SESSION TIMEOUT ---
if st.session_state.logged_in and st.session_state.last_activity > 0:
    idle = time.time() - st.session_state.last_activity
    if idle > SESSION_TIMEOUT_SECONDS:
        st.session_state.logged_in = False
        st.session_state.current_user = "unknown"
        st.session_state.login_attempts = 0
        st.session_state.ignore_cookie = True
        st.toast("Session expired. Please sign in again.")
        st.rerun()
    else:
        st.session_state.last_activity = time.time()

if not st.session_state.logged_in:
    auth_cookie = cookies.get("auth_user") if cookies else None
    if auth_cookie and not st.session_state.get("ignore_cookie"):
        st.session_state.logged_in = True
        st.session_state.current_user = auth_cookie
        st.session_state.last_activity = time.time()
        st.rerun()

if not st.session_state.logged_in:
    inject_css("login.css")

    if st.session_state.get("login_success"):
        st.markdown("<div style='max-width: 400px; margin: 0 auto; background-color: #FFFFFF; border: 3px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; padding: 16px 20px; margin-top: 16px;'><p style='color: #0F172A; font-family: \"Source Sans 3\", sans-serif; font-size: 1.1rem; font-weight: 800; margin: 0; text-align: center;'>Authentication Successful.<br>Welcome Back!</p></div>", unsafe_allow_html=True)
        cookie_manager.set("auth_user", st.session_state.current_user, max_age=86400 * 7) # 7 days
        time.sleep(1.2)
        st.session_state.logged_in = True
        st.session_state.ignore_cookie = False
        del st.session_state["login_success"]
        st.rerun()
    else:
        with st.form("login_form"):
            st.markdown(
                "<div style='text-align: center; margin-bottom: 24px;'>"
                "<div style='display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background-color: #FFDE59; border: 3px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; margin-bottom: 16px;'>"
                "<svg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 24 24' fill='none' stroke='#0F172A' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'>"
                "<rect x='3' y='11' width='18' height='11' rx='2' ry='2'></rect>"
                "<path d='M7 11V7a5 5 0 0 1 10 0v4'></path>"
                "</svg>"
                "</div>"
                "<div style='color: #0F172A; font-weight: 800; font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; font-size: 1.4rem; margin: 0; padding: 0; letter-spacing: -0.02em;'>Sign In</div>"
                "</div>", 
                unsafe_allow_html=True
            )
            username = st.text_input("Username", placeholder="")
            password = st.text_input("Password", type="password", placeholder="")
            
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            
            submit = st.form_submit_button("LOGIN", type="primary", use_container_width=True)
            
            if submit:
                if username:
                    username = username.strip().title()
                
                if not username:
                    st.markdown("<div style='background-color: #FFFFFF; border: 3px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; padding: 12px 16px; margin-top: 16px;'><p style='color: #0F172A; font-family: \"Source Sans 3\", sans-serif; font-size: 0.9rem; font-weight: 700; margin: 0; text-align: center;'>Please enter a username.</p></div>", unsafe_allow_html=True)
                else:
                    is_locked, remaining, attempts = database.check_login_lockout(supabase, username)
                    
                    if is_locked:
                        st.markdown(f"<div style='background-color: #FFFFFF; border: 3px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; padding: 12px 16px; margin-top: 16px;'><p style='color: #0F172A; font-family: \"Source Sans 3\", sans-serif; font-size: 0.9rem; font-weight: 700; margin: 0; text-align: center;'>Account locked. Please try again in {remaining} seconds.</p></div>", unsafe_allow_html=True)
                    else:
                        if database.authenticate_user(supabase, username, password):
                            database.reset_failed_login(supabase, username)
                            st.session_state.login_success = True
                            st.session_state.current_user = username
                            st.session_state.last_activity = time.time()
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
    with st.expander("What's New & Changelog", expanded=False):
        try:
            with open("CHANGELOG.md", "r", encoding="utf-8") as f:
                lines = f.readlines()
            start_idx = 0
            for idx, line in enumerate(lines):
                if line.strip().startswith("###"):
                    start_idx = idx
                    break
            changelog_content = "".join(lines[start_idx:])
            
            # Neo-Brutalist Changelog Headers
            changelog_content = changelog_content.replace(
                "### ✨ Fitur Baru", 
                "<h3><span style='background: #A3E635; border: 3px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; padding: 4px 12px; font-weight: 900; font-family: \"Source Sans 3\", sans-serif; letter-spacing: 0.05em; text-transform: uppercase;'>NEW FEATURES</span></h3>\n\n"
            )
            changelog_content = changelog_content.replace(
                "### 🛠️ Perbaikan & Peningkatan", 
                "<h3><span style='background: #FBBF24; border: 3px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; padding: 4px 12px; font-weight: 900; font-family: \"Source Sans 3\", sans-serif; letter-spacing: 0.05em; text-transform: uppercase;'>IMPROVEMENTS</span></h3>\n\n"
            )
            st.markdown(changelog_content, unsafe_allow_html=True)
        except Exception:
            pass

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

nav_pages = [dashboard_page, inventory_page, sales_page, promotion_page, mutation_page, clearance_page, initial_page]

if os.path.exists("pages/7_element_crawler.py"):
    crawler_page = st.Page("pages/7_element_crawler.py", title="Element Crawler", url_path="crawler")
    nav_pages.append(crawler_page)

# Run navigation
pg = st.navigation(nav_pages, position="hidden")
pg.run()

