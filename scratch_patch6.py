import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add extra_streamlit_components import
if 'import extra_streamlit_components as stx' not in content:
    content = content.replace(
        'import streamlit as st',
        'import streamlit as st\nimport extra_streamlit_components as stx'
    )

# Add cookie manager logic
cookie_manager_code = """
@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()
# Let the cookie manager initialize
# It needs a run to fetch cookies from the client
if cookie_manager.get_all() is None:
    st.stop()
"""

if 'def get_cookie_manager():' not in content:
    # Insert right before MAX_LOGIN_ATTEMPTS
    content = content.replace(
        'MAX_LOGIN_ATTEMPTS = 5',
        cookie_manager_code + '\nMAX_LOGIN_ATTEMPTS = 5'
    )

# Replace the login check block
old_check_block = """if not st.session_state.logged_in:
    inject_css("login.css")"""

new_check_block = """if not st.session_state.logged_in:
    auth_cookie = cookie_manager.get(cookie="auth_user")
    if auth_cookie:
        st.session_state.logged_in = True
        st.session_state.current_user = auth_cookie
        st.session_state.last_activity = time.time()
        st.rerun()

if not st.session_state.logged_in:
    inject_css("login.css")"""

if 'auth_cookie = cookie_manager.get' not in content:
    content = content.replace(old_check_block, new_check_block)

# Replace the successful login block
old_success = """                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.session_state.last_activity = time.time()
                        time.sleep(1.2)
                        st.rerun()"""

new_success = """                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.session_state.last_activity = time.time()
                        cookie_manager.set("auth_user", username, max_age=86400 * 7) # 7 days
                        time.sleep(1.2)
                        st.rerun()"""

if 'cookie_manager.set("auth_user"' not in content:
    content = content.replace(old_success, new_success)

# Replace session timeout logic to optionally delete cookie?
# The user wants it to be persistent, so maybe we don't time it out strictly if the cookie is there.
# If they are idle, should we log them out? They said "bisa ditinggal tidur, nggak gampang minta login lagi".
# Let's remove the session timeout forced logout, or increase it to 24 hours.
old_timeout = "SESSION_TIMEOUT_SECONDS = 3600  # 1 hour"
new_timeout = "SESSION_TIMEOUT_SECONDS = 86400 * 7  # 7 days"
content = content.replace(old_timeout, new_timeout)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched app.py with cookie manager")
