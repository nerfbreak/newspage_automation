import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I will replace the `with st.form("login_form"):` part with the new logic.
old_block = """    with st.form("login_form"):
        st.markdown(
            "<div style='text-align: center; margin-bottom: 24px;'>"
            "<div style='display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background-color: #FFDE59; border: 3px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; margin-bottom: 16px;'>"
            "<svg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 24 24' fill='none' stroke='#0F172A' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'>"
            "<rect x='3' y='11' width='18' height='11' rx='2' ry='2'></rect>"
            "<path d='M7 11V7a5 5 0 0 1 10 0v4'></path>"
            "</svg>"
            "</div>"
            "<div style='color: #0F172A; font-weight: 800; font-family: \\"Source Sans 3\\", \\"Source Sans Pro\\", sans-serif; font-size: 1.4rem; margin: 0; padding: 0; letter-spacing: -0.02em;'>Sign In</div>"
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
                st.markdown("<div style='background-color: #FFFFFF; border: 3px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; padding: 12px 16px; margin-top: 16px;'><p style='color: #0F172A; font-family: \\"Source Sans 3\\", sans-serif; font-size: 0.9rem; font-weight: 700; margin: 0; text-align: center;'>Please enter a username.</p></div>", unsafe_allow_html=True)
            else:
                is_locked, remaining, attempts = database.check_login_lockout(supabase, username)
                
                if is_locked:
                    st.markdown(f"<div style='background-color: #FFFFFF; border: 3px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; padding: 12px 16px; margin-top: 16px;'><p style='color: #0F172A; font-family: \\"Source Sans 3\\", sans-serif; font-size: 0.9rem; font-weight: 700; margin: 0; text-align: center;'>Account locked. Please try again in {remaining} seconds.</p></div>", unsafe_allow_html=True)
                else:
                    if database.authenticate_user(supabase, username, password):
                        database.reset_failed_login(supabase, username)
                        st.markdown("<div style='background-color: #FFFFFF; border: 3px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; padding: 12px 16px; margin-top: 16px;'><p style='color: #0F172A; font-family: \\"Source Sans 3\\", sans-serif; font-size: 0.9rem; font-weight: 700; margin: 0; text-align: center;'>Authentication Successful. Welcome Back.</p></div>", unsafe_allow_html=True)
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.session_state.last_activity = time.time()
                        cookie_manager.set("auth_user", username, max_age=86400 * 7) # 7 days
                        time.sleep(1.2)
                        st.rerun()
                    else:
                        database.record_failed_login(supabase, username, max_attempts=MAX_LOGIN_ATTEMPTS, lockout_minutes=LOCKOUT_SECONDS // 60)
                        _, _, new_attempts = database.check_login_lockout(supabase, username)
                        attempts_left = max(0, MAX_LOGIN_ATTEMPTS - new_attempts)
                        
                        if new_attempts >= MAX_LOGIN_ATTEMPTS:
                            send_telegram_alert(f"[ALERT] Account lockout triggered for user: <b>{_html.escape(username)}</b>\\n{MAX_LOGIN_ATTEMPTS} failed attempts.")
                            st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Account locked for {LOCKOUT_SECONDS // 60} minutes due to too many failed attempts.</p>", unsafe_allow_html=True)
                        else:
                            time.sleep(1.5)  # Slow down brute-force attempts
                            st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Invalid credentials. {attempts_left} attempt(s) remaining.</p>", unsafe_allow_html=True)"""


new_block = """    if st.session_state.get("login_success"):
        st.markdown("<div style='max-width: 400px; margin: 0 auto; background-color: #FFFFFF; border: 3px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; padding: 16px 20px; margin-top: 16px;'><p style='color: #0F172A; font-family: \"Source Sans 3\", sans-serif; font-size: 1.1rem; font-weight: 800; margin: 0; text-align: center;'>Authentication Successful.<br>Welcome Back!</p></div>", unsafe_allow_html=True)
        cookie_manager.set("auth_user", st.session_state.current_user, max_age=86400 * 7) # 7 days
        time.sleep(1.2)
        st.session_state.logged_in = True
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
                                send_telegram_alert(f"[ALERT] Account lockout triggered for user: <b>{_html.escape(username)}</b>\\n{MAX_LOGIN_ATTEMPTS} failed attempts.")
                                st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Account locked for {LOCKOUT_SECONDS // 60} minutes due to too many failed attempts.</p>", unsafe_allow_html=True)
                            else:
                                time.sleep(1.5)  # Slow down brute-force attempts
                                st.markdown(f"<p style='color: #FF2B2B; font-size: 0.8rem; text-align: center; margin-top: 10px;'>Invalid credentials. {attempts_left} attempt(s) remaining.</p>", unsafe_allow_html=True)"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched app.py logic")
else:
    print("Could not find block")
