import streamlit as st
import pandas as pd
import database
import playwright_engine
from utils import (
    render_header, render_footer, check_auth,
    make_solid_box, init_session_state,
    make_terminal_logger, render_terminal
)

check_auth()
supabase = database.init_supabase()
_sys_cfg = database.get_system_config(supabase)
URL_LOGIN = _sys_cfg.get("URL_LOGIN", "")

init_session_state(
    crawler_results=None,
    is_crawling=False,
    ext_logs=[]
)

render_header("Element Crawler")

st.markdown("""
<div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 24px;'>
    <h3 style='margin: 0 0 12px 0; color: #0F172A; font-size: 1.1rem;'>🎯 Element ID Extractor</h3>
    <p style='color: #475569; font-size: 0.9rem; margin: 0;'>Alat rahasia ini akan melakukan login otomatis ke portal Accenture dan mengekstrak semua elemen interaktif (button, input, select, link) pada halaman yang dituju. Sangat berguna untuk inspeksi struktur DOM tanpa perlu login manual.</p>
</div>
""", unsafe_allow_html=True)

# Fetch Distributors
if "distributor_list" not in st.session_state:
    try:
        res = supabase.table("distributor_vault").select("nama_distributor, np_user_id, np_password").execute()
        st.session_state.distributor_list = res.data if res.data else []
    except Exception as e:
        st.session_state.distributor_list = []
        st.error(f"Gagal memuat distributor: {e}")

dist_list = st.session_state.distributor_list
dist_names = [d["nama_distributor"] for d in dist_list]

col1, col2 = st.columns([1, 1])
with col1:
    selected_dist = st.selectbox("Gunakan Akun Distributor", options=dist_names)
with col2:
    target_path = st.text_input("Target URL Path (Opsional)", placeholder="/Sales/Order")

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

btn_disabled = st.session_state.is_crawling
if st.button("🕷️ Start Crawling", type="primary", use_container_width=True, disabled=btn_disabled):
    st.session_state.is_crawling = True
    st.session_state.crawler_results = None
    st.session_state.ext_logs = []
    st.rerun()

if st.session_state.is_crawling:
    st.info("Bot sedang berjalan... Mengekstrak elemen HTML...")
    term_ph = st.empty()
    logger, _ = make_terminal_logger(term_ph)
    
    sel_d = next((d for d in dist_list if d["nama_distributor"] == selected_dist), None)
    if not sel_d:
        st.error("Distributor tidak ditemukan.")
        st.session_state.is_crawling = False
        st.rerun()
        
    user, pwd = database.get_distributor_creds(supabase, selected_dist)
    
    try:
        results = playwright_engine.run_element_crawler(user, pwd, selected_dist, URL_LOGIN, target_path, logger)
        st.session_state.crawler_results = results
    except Exception as e:
        st.session_state.crawler_error = str(e)
    finally:
        st.session_state.is_crawling = False
        st.rerun()

if st.session_state.get("crawler_error"):
    st.error(f"Crawling gagal: {st.session_state.crawler_error}")
    # Show logs so they can see where it failed
    if st.session_state.ext_logs:
        st.markdown("### Terminal Logs")
        for log in st.session_state.ext_logs:
            st.markdown(log, unsafe_allow_html=True)
    if st.button("Tutup Pesan Error"):
        st.session_state.crawler_error = None
        st.session_state.ext_logs = []
        st.rerun()

if st.session_state.crawler_results is not None:
    results = st.session_state.crawler_results
    if len(results) == 0:
        st.warning("Tidak ada elemen yang berhasil diekstrak.")
    else:
        st.success(f"Berhasil mengekstrak {len(results)} elemen interaktif!")
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"elements_{selected_dist}.csv",
            mime="text/csv",
        )

render_footer()
