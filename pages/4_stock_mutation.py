import pandas as pd
import streamlit as st
import utils
import database
import data_processor
import playwright_engine
from database import EXCLUDE_PREFIX
from utils import (
    render_footer, make_solid_box, render_metric_card,
    check_auth, render_indicators, render_header,
    send_telegram_alert, init_session_state, render_wakelock,
    safe_parse_numeric,
)
from error_taxonomy import format_user_error


# --- AUTH CHECK ---
check_auth()

supabase = database.init_supabase()
_sys_cfg = database.get_system_config(supabase)
REASON_CODE = _sys_cfg["REASON_CODE"]
WAREHOUSE   = _sys_cfg["WAREHOUSE"]
URL_LOGIN   = _sys_cfg["URL_LOGIN"]
TIMEOUT_MS  = _sys_cfg["TIMEOUT_MS"]
TABLE_UPDATE_INTERVAL = _sys_cfg["TABLE_UPDATE_INTERVAL"]

# --- STATE MANAGEMENT ---
init_session_state(
    is_mutasi_running=False,
    mutasi_review_df=None,
    mutasi_file_id=None,
    mutasi_uploader_key=0,
    selected_reason_code="",
    remark_a="",
    remark_b="",
    mutasi_execute_done=False,
    mutasi_shot_a=None,
    mutasi_shot_b=None,
    mutasi_msg_a="",
    mutasi_msg_b=""
)


def _clear_mutasi_upload():
    st.session_state.mutasi_uploader_key += 1
    st.session_state.mutasi_file_id = None
    st.session_state.mutasi_review_df = None


render_wakelock()

# --- MAIN UI ---
db_status = "CONNECTED" if supabase is not None else "DISCONNECTED"
bot_status = "RUNNING" if st.session_state.is_mutasi_running else "STANDBY"

render_indicators(db_status, bot_status, bot_type="MUTASI ENGINE")
render_header("Mutasi Stock", st.session_state.current_user)





# --- DISTRIBUTOR SELECTION ---
col1, col2 = st.columns(2)

list_dist = database.get_distributor_list(supabase)

with col1:
    st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
    with st.container(border=True):
        dist_a = st.selectbox("Pilih Distributor Pengirim", list_dist, key="mutasi_dist_a")
        bot_user_a, bot_pass_a = database.get_distributor_creds(supabase, dist_a)

with col2:
    st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
    with st.container(border=True):
        # Filter out dist_a from receiver list to prevent same-distributor selection
        list_dist_b = [d for d in list_dist if d != dist_a]
        dist_b = st.selectbox("Pilih Distributor Penerima", list_dist_b, key="mutasi_dist_b")
        bot_user_b, bot_pass_b = database.get_distributor_creds(supabase, dist_b)

# --- FILE UPLOAD + COLUMN MAPPING ---
df_raw = None
st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True):
    uploaded_file = st.file_uploader("Upload file Excel berisi SKU yang akan dimutasi", type=['csv', 'xlsx', 'xls'], key=f"mutasi_file_uploader_{st.session_state.mutasi_uploader_key}")

    # Track file changes to reset state
    curr_file_id = getattr(uploaded_file, "file_id", uploaded_file.name if uploaded_file else None) if uploaded_file else None
    if curr_file_id != st.session_state.mutasi_file_id:
        st.session_state.mutasi_file_id = curr_file_id
        st.session_state.mutasi_review_df = None

    if uploaded_file is not None:
        df_raw = data_processor.load_data(uploaded_file)

    if df_raw is not None and not df_raw.empty:
        st.markdown(f"""
            <style>
                div[data-testid="stFileUploader"] section {{ display: none !important; }}
                div[data-testid="stFileUploader"] {{ margin-bottom: -1rem !important; padding-bottom: 0px !important; }}
            </style>
            {make_solid_box(f"FILE LOADED: {uploaded_file.name}", "#FFDE59", "#0F172A")}
        """, unsafe_allow_html=True)
        
        # Show uploaded raw data preview
        st.markdown("<div class='header-wrapper-center-notop'><span class='section-header-underline'>Preview Uploaded Data</span></div>", unsafe_allow_html=True)
        st.dataframe(df_raw.head(5), use_container_width=True, hide_index=True)
        
        st.markdown("<span class='red-btn-marker'></span>", unsafe_allow_html=True)
        st.button(
            "Hapus File Upload",
            type="secondary",
            width='stretch',
            icon=":material/delete:",
            on_click=_clear_mutasi_upload,
        )
    elif uploaded_file is not None:
        st.error(format_user_error("UPLOAD-001"))

if uploaded_file is not None and df_raw is not None and not df_raw.empty:
    # --- COLUMN MAPPING ---
    st.markdown("<div class='header-wrapper-center-notop'><span class='section-header-underline'>Column Mapping</span></div>", unsafe_allow_html=True)
    mc1, mc2, mc3 = st.columns(3)

    with mc1:
        st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
        with st.container(border=True):
            # Auto-detect SKU column
            sku_candidates = [c for c in df_raw.columns if any(k in str(c).lower() for k in ['sku', 'code', 'kode', 'produk'])]
            idx_sku = df_raw.columns.get_loc(sku_candidates[0]) if sku_candidates else 0
            sku_col = st.selectbox("SKU Column", df_raw.columns, index=idx_sku, key="mutasi_sku_col")
            sku_metric_ph = st.empty()

    with mc2:
        st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
        with st.container(border=True):
            # Auto-detect Description column
            desc_candidates = [c for c in df_raw.columns if any(k in str(c).lower() for k in ['desc', 'name', 'nama', 'produk'])]
            idx_desc = df_raw.columns.get_loc(desc_candidates[0]) if desc_candidates else (1 if len(df_raw.columns) > 1 else 0)
            desc_col = st.selectbox("Description Column", df_raw.columns, index=idx_desc, key="mutasi_desc_col")
            deduct_metric_ph = st.empty()

    with mc3:
        st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
        with st.container(border=True):
            # Auto-detect Qty column
            qty_candidates = [c for c in df_raw.columns if any(k in str(c).lower() for k in ['qty', 'stock', 'stok', 'jumlah', 'mutasi'])]
            idx_qty = df_raw.columns.get_loc(qty_candidates[0]) if qty_candidates else (2 if len(df_raw.columns) > 2 else 0)
            qty_col = st.selectbox("Qty Column", df_raw.columns, index=idx_qty, key="mutasi_qty_col")
            add_metric_ph = st.empty()

    # --- BUILD REVIEW TABLE ---
    df_review = df_raw[[sku_col, desc_col, qty_col]].copy()
    df_review.columns = ['SKU', 'Description', 'Qty']

    # Clean data
    TARGET_SKUS = database.get_target_skus(supabase)
    df_review = data_processor.clean_sku_column(df_review, 'SKU', TARGET_SKUS)
    df_review['Qty'] = df_review['Qty'].apply(safe_parse_numeric).astype(int)
    df_review = df_review[df_review['Qty'] != 0].reset_index(drop=True)

    if len(df_review) > 0:
        st.session_state.mutasi_review_df = df_review

        # Summary metrics
        sku_metric_ph.markdown(render_metric_card("Total SKU", len(df_review)), unsafe_allow_html=True)
        deduct_metric_ph.markdown(render_metric_card(f"Total Qty Dikurangi ({dist_a})", f"-{df_review['Qty'].sum()}"), unsafe_allow_html=True)
        add_metric_ph.markdown(render_metric_card(f"Total Qty Ditambah ({dist_b})", f"+{df_review['Qty'].sum()}"), unsafe_allow_html=True)

        # Review table with deduction/addition preview
        df_display = df_review.copy()
        df_display[f'Deduct ({dist_a})'] = df_display['Qty'].apply(lambda x: f"-{abs(x)}")
        df_display[f'Add ({dist_b})'] = df_display['Qty'].apply(lambda x: f"+{abs(x)}")
        
        st.markdown("<div class='header-wrapper-center'><span class='section-header-underline'>Stock Review</span></div>", unsafe_allow_html=True)
        utils.render_responsive_dataframe(df_display[['SKU', 'Description', 'Qty', f'Deduct ({dist_a})', f'Add ({dist_b})']])
    else:
        st.warning("Tidak ada SKU valid di file yang diupload.")

# --- EXECUTE ---
review_ready = st.session_state.mutasi_review_df is not None and len(st.session_state.mutasi_review_df) > 0
can_execute = review_ready and bot_user_a and bot_pass_a and bot_user_b and bot_pass_b and not st.session_state.is_mutasi_running

st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True):
    with st.form(key="mutasi_execute_form", border=False):
        reason_options = {
            "SA1": "SA1 - Transformasi Kode Barang",
            "SA2": "SA2 - Selisih Barang",
            "SA3": "SA3 - Transfer Gudang Internal",
            "SA4": "SA4 - Transfer Gudang External"
        }
        default_reason_idx = 0
        for i, key in enumerate(reason_options.keys()):
            if key == REASON_CODE:
                default_reason_idx = i
                break
        selected_reason_label = st.selectbox("Reason Adjustment", list(reason_options.values()), index=default_reason_idx, key="mutasi_reason")
        selected_reason_code = [k for k, v in reason_options.items() if v == selected_reason_label][0]
        
        c1, c2 = st.columns(2)
        with c1:
            remark_a = st.text_input("Remark Pengirim", max_chars=50, key="mutasi_remark_a")
        with c2:
            remark_b = st.text_input("Remark Penerima", max_chars=50, key="mutasi_remark_b")
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        execute_clicked = st.form_submit_button("Execute", type="primary", use_container_width=True, disabled=not can_execute, icon=":material/play_arrow:")

if execute_clicked:
    st.session_state.is_mutasi_running = True
    st.session_state.selected_reason_code = selected_reason_code
    st.session_state.remark_a = remark_a
    st.session_state.remark_b = remark_b
    st.rerun()

if st.session_state.is_mutasi_running:
    df_mutasi = st.session_state.mutasi_review_df.copy()

    # Dual layout
    st.markdown("<span class='mutation-execution-layout-marker'></span>", unsafe_allow_html=True)
    exec_col1, exec_col2 = st.columns(2)

    with exec_col1:
        st.markdown(f"""
            <div style='background-color: #FF2B2B; color: #FFFFFF; font-family: "Source Sans 3", sans-serif; font-size: 0.85rem; font-weight: 800; padding: 6px 12px; border: 2px solid #0F172A; box-shadow: 2px 2px 0px 0px #0F172A; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px; margin-top: 10px; display: flex; align-items: center; justify-content: center; min-height: 52px; text-align: center;'>
                DEDUCT &nbsp;|&nbsp; <span style='font-size: 0.72rem; opacity: 0.9;'>{dist_a} ({bot_user_a})</span>
            </div>
        """, unsafe_allow_html=True)
        table_a_ph = st.empty()
        prog_a_ph = st.empty()

    with exec_col2:
        st.markdown(f"""
            <div style='background-color: #09A53C; color: #FFFFFF; font-family: "Source Sans 3", sans-serif; font-size: 0.85rem; font-weight: 800; padding: 6px 12px; border: 2px solid #0F172A; box-shadow: 2px 2px 0px 0px #0F172A; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px; margin-top: 10px; display: flex; align-items: center; justify-content: center; min-height: 52px; text-align: center;'>
                ADD &nbsp;|&nbsp; <span style='font-size: 0.72rem; opacity: 0.9;'>{dist_b} ({bot_user_b})</span>
            </div>
        """, unsafe_allow_html=True)
        table_b_ph = st.empty()
        prog_b_ph = st.empty()

    # Initial table render
    df_a_display = df_mutasi[['SKU', 'Description', 'Qty']].copy()
    df_a_display['Qty'] = '-' + df_a_display['Qty'].astype(str)
    df_a_display['Status'] = 'Pending'
    df_a_display['Keterangan'] = 'Ready'
    utils.render_responsive_dataframe(table_a_ph, df_a_display, fixed_height=400)

    df_b_display = df_mutasi[['SKU', 'Description', 'Qty']].copy()
    df_b_display['Status'] = 'Pending'
    df_b_display['Keterangan'] = 'Ready'
    utils.render_responsive_dataframe(table_b_ph, df_b_display, fixed_height=400)

    prog_a_ph.progress(0)
    prog_b_ph.progress(0)

    # Terminal log placeholders
    log_label_a_ph = st.empty()
    log_a_ph = st.empty()
    log_label_b_ph = st.empty()
    log_b_ph = st.empty()



    # Execute — engine handles log rendering internally
    try:
        playwright_engine.run_mutasi_execution(
            df_mutasi,
            bot_user_a, bot_pass_a, dist_a,
            bot_user_b, bot_pass_b, dist_b,
            URL_LOGIN, TIMEOUT_MS, WAREHOUSE, WAREHOUSE,
            st.session_state.selected_reason_code, TABLE_UPDATE_INTERVAL,
            send_telegram_alert,
            table_a_ph, table_b_ph,
            prog_a_ph, prog_b_ph,
            log_a_ph, log_b_ph,
            supabase,
            remark_text_a=st.session_state.remark_a,
            remark_text_b=st.session_state.remark_b,
            current_user=st.session_state.current_user,
        )
    finally:
        st.session_state.is_mutasi_running = False
        # Clear review state after execution
        st.session_state.mutasi_review_df = None



if st.session_state.get("mutasi_execute_done"):
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    import os
    import base64
    import re
    import streamlit.components.v1 as components
    
    with st.expander("BUKTI TRANSAKSI (SCREENSHOT)", expanded=False):
        st.markdown("""
        <div style="background-color: #dbeafe; color: #1e3a8a; padding: 12px 16px; border-radius: 0px; font-size: 0.85rem; font-weight: 700; border: 3px solid #0F172A; margin-bottom: 24px; box-shadow: 6px 6px 0px 0px #0F172A; display: flex; align-items: center; gap: 12px; margin-top: 12px;">
            <span style="font-size: 1.2rem;">ℹ</span>
            <span>Pekerjaan selesai! Screenshot berhasil ditangkap.</span>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='header-wrapper-center-notop'><span class='section-header-underline'>PENGIRIM (DEDUCT)</span></div>", unsafe_allow_html=True)
            shot_a = st.session_state.get("mutasi_shot_a")
            msg_a = st.session_state.get("mutasi_msg_a", "")
            if shot_a and os.path.exists(shot_a):
                with open(shot_a, "rb") as f: b64_a = base64.b64encode(f.read()).decode("utf-8")
                
                plain_msg_a = re.sub(r'<b>(.*?)</b>', r'*\1*', msg_a)
                plain_msg_a = re.sub(r'<[^>]+>', '', plain_msg_a)
                js_msg_a = plain_msg_a.replace('\n', '\\n').replace('"', '\\"').replace("'", "\\'")
                
                button_html_a = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                  @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700;800&display=swap');
                  body {{ margin: 0; padding: 4px 10px 10px 4px; display: flex; gap: 12px; overflow: hidden; font-family: 'Source Sans 3', sans-serif; }}
                  .neo-btn {{ flex: 1; display: inline-flex; align-items: center; justify-content: center; height: 42px; background-color: #0068C9; color: #FFFFFF; border: 2px solid #0F172A; border-radius: 0px; font-weight: 800; font-size: 0.85rem; letter-spacing: 0.04em; text-transform: uppercase; text-decoration: none; box-shadow: 4px 4px 0px 0px #0F172A; cursor: pointer; transition: all 0.1s; box-sizing: border-box; padding: 0 8px; }}
                  .neo-btn:hover {{ transform: translate(2px, 2px); box-shadow: 2px 2px 0px 0px #0F172A; }}
                  .neo-btn:active {{ transform: translate(4px, 4px); box-shadow: 0px 0px 0px 0px #0F172A; }}
                  .neo-btn.success {{ background-color: #10B981; }}
                  svg {{ margin-right: 6px; }}
                </style>
                <script>
                let preloadedBlobItem = null;
                const textToCopy = "{js_msg_a}";

                async function preloadImage() {{
                    try {{
                        const res = await fetch("data:image/png;base64,{b64_a}");
                        const blob = await res.blob();
                        preloadedBlobItem = new ClipboardItem({{"image/png": blob}});
                    }} catch (e) {{ console.error("Preload failed", e); }}
                }}
                window.addEventListener("DOMContentLoaded", preloadImage);

                function showSuccess(btn, originalHtml) {{
                    btn.innerHTML = '✔ DISALIN!';
                    btn.classList.add('success');
                    setTimeout(() => {{ btn.innerHTML = originalHtml; btn.classList.remove('success'); }}, 2000);
                }}

                function copyImage(event) {{
                    const btn = event.currentTarget;
                    const originalHtml = btn.innerHTML;
                    if (preloadedBlobItem) {{
                        navigator.clipboard.write([preloadedBlobItem]).then(() => {{ showSuccess(btn, originalHtml); }})
                        .catch(err => {{ alert("Gagal copy gambar. Browser mungkin tidak support."); }});
                    }} else {{ alert("Gambar sedang disiapkan, tunggu sebentar."); }}
                }}

                function copyText(event) {{
                    const btn = event.currentTarget;
                    const originalHtml = btn.innerHTML;
                    navigator.clipboard.writeText(textToCopy).then(() => {{ showSuccess(btn, originalHtml); }})
                    .catch(err => {{ alert("Gagal copy teks."); }});
                }}
                </script>
                </head>
                <body>
                  <a href="data:image/png;base64,{b64_a}" download="{os.path.basename(shot_a)}" class="neo-btn" style="background-color: #F8FAFC; color: #0F172A;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg> UNDUH
                  </a>
                  <button class="neo-btn" onclick="copyImage(event)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg> COPY GAMBAR
                  </button>
                  <button class="neo-btn" onclick="copyText(event)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="square" stroke-linejoin="miter" d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg> COPY TEKS
                  </button>
                </body>
                </html>
                """
                components.html(button_html_a, height=60)
                st.markdown(f'<div style="border: 3px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; margin-bottom: 16px; padding: 4px; background: #FFF;"><img src="data:image/png;base64,{b64_a}" style="width: 100%; display: block;"/></div>', unsafe_allow_html=True)
            else:
                st.info("Screenshot Pengirim tidak tersedia.")
                
        with c2:
            st.markdown("<div class='header-wrapper-center-notop'><span class='section-header-underline'>PENERIMA (ADD)</span></div>", unsafe_allow_html=True)
            shot_b = st.session_state.get("mutasi_shot_b")
            msg_b = st.session_state.get("mutasi_msg_b", "")
            if shot_b and os.path.exists(shot_b):
                with open(shot_b, "rb") as f: b64_b = base64.b64encode(f.read()).decode("utf-8")
                
                plain_msg_b = re.sub(r'<b>(.*?)</b>', r'*\1*', msg_b)
                plain_msg_b = re.sub(r'<[^>]+>', '', plain_msg_b)
                js_msg_b = plain_msg_b.replace('\n', '\\n').replace('"', '\\"').replace("'", "\\'")
                
                button_html_b = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                  @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700;800&display=swap');
                  body {{ margin: 0; padding: 4px 10px 10px 4px; display: flex; gap: 12px; overflow: hidden; font-family: 'Source Sans 3', sans-serif; }}
                  .neo-btn {{ flex: 1; display: inline-flex; align-items: center; justify-content: center; height: 42px; background-color: #0068C9; color: #FFFFFF; border: 2px solid #0F172A; border-radius: 0px; font-weight: 800; font-size: 0.85rem; letter-spacing: 0.04em; text-transform: uppercase; text-decoration: none; box-shadow: 4px 4px 0px 0px #0F172A; cursor: pointer; transition: all 0.1s; box-sizing: border-box; padding: 0 8px; }}
                  .neo-btn:hover {{ transform: translate(2px, 2px); box-shadow: 2px 2px 0px 0px #0F172A; }}
                  .neo-btn:active {{ transform: translate(4px, 4px); box-shadow: 0px 0px 0px 0px #0F172A; }}
                  .neo-btn.success {{ background-color: #10B981; }}
                  svg {{ margin-right: 6px; }}
                </style>
                <script>
                let preloadedBlobItem = null;
                const textToCopy = "{js_msg_b}";

                async function preloadImage() {{
                    try {{
                        const res = await fetch("data:image/png;base64,{b64_b}");
                        const blob = await res.blob();
                        preloadedBlobItem = new ClipboardItem({{"image/png": blob}});
                    }} catch (e) {{ console.error("Preload failed", e); }}
                }}
                window.addEventListener("DOMContentLoaded", preloadImage);

                function showSuccess(btn, originalHtml) {{
                    btn.innerHTML = '✔ DISALIN!';
                    btn.classList.add('success');
                    setTimeout(() => {{ btn.innerHTML = originalHtml; btn.classList.remove('success'); }}, 2000);
                }}

                function copyImage(event) {{
                    const btn = event.currentTarget;
                    const originalHtml = btn.innerHTML;
                    if (preloadedBlobItem) {{
                        navigator.clipboard.write([preloadedBlobItem]).then(() => {{ showSuccess(btn, originalHtml); }})
                        .catch(err => {{ alert("Gagal copy gambar. Browser mungkin tidak support."); }});
                    }} else {{ alert("Gambar sedang disiapkan, tunggu sebentar."); }}
                }}

                function copyText(event) {{
                    const btn = event.currentTarget;
                    const originalHtml = btn.innerHTML;
                    navigator.clipboard.writeText(textToCopy).then(() => {{ showSuccess(btn, originalHtml); }})
                    .catch(err => {{ alert("Gagal copy teks."); }});
                }}
                </script>
                </head>
                <body>
                  <a href="data:image/png;base64,{b64_b}" download="{os.path.basename(shot_b)}" class="neo-btn" style="background-color: #F8FAFC; color: #0F172A;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg> UNDUH
                  </a>
                  <button class="neo-btn" onclick="copyImage(event)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg> COPY GAMBAR
                  </button>
                  <button class="neo-btn" onclick="copyText(event)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="square" stroke-linejoin="miter" d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg> COPY TEKS
                  </button>
                </body>
                </html>
                """
                components.html(button_html_b, height=60)
                st.markdown(f'<div style="border: 3px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; margin-bottom: 16px; padding: 4px; background: #FFF;"><img src="data:image/png;base64,{b64_b}" style="width: 100%; display: block;"/></div>', unsafe_allow_html=True)
            else:
                st.info("Screenshot Penerima tidak tersedia.")

render_footer()
