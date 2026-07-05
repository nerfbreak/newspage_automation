import os
import html
import base64
import logging
import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────
# URL_LOGIN, TIMEOUT_MS, TABLE_UPDATE_INTERVAL are now stored in Supabase (system_config table)
# and fetched via database.get_system_config(supabase).


# ── Param encoding (shared across all pages) ──────────────
def encode_param(val: str) -> str:
    if not val:
        return ""
    try:
        return base64.urlsafe_b64encode(val.encode("utf-8")).decode("utf-8")
    except Exception:
        return val


def decode_param(encoded: str) -> str:
    if not encoded:
        return ""
    try:
        return base64.urlsafe_b64decode(encoded.encode("utf-8")).decode("utf-8")
    except Exception:
        return encoded


# ── Telegram alerts (shared across all pages) ─────────────
def _send_sync(url, payload, files=None, local_path_to_delete=None):
    try:
        if files:
            requests.post(url, data=payload, files=files, timeout=15)
        else:
            requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.warning(f"Telegram alert failed: {e}")
    finally:
        if local_path_to_delete and os.path.exists(local_path_to_delete):
            try:
                os.remove(local_path_to_delete)
                logger.info(f"Deleted local screenshot: {local_path_to_delete}")
            except Exception as delete_err:
                logger.warning(f"Failed to delete local screenshot {local_path_to_delete}: {delete_err}")

def send_telegram_alert(message: str, photo_path: str = None, delete_after: bool = True):
    bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if bot_token and chat_id:
        import threading, os
        if photo_path and os.path.exists(photo_path):
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            payload = {"chat_id": chat_id, "caption": message, "parse_mode": "HTML"}
            # Pass data in memory so thread does not keep file locked
            try:
                with open(photo_path, 'rb') as f:
                    file_data = f.read()
                files = {"photo": (os.path.basename(photo_path), file_data)}
                path_to_delete = photo_path if delete_after else None
                threading.Thread(target=_send_sync, args=(url, payload, files, path_to_delete), daemon=True).start()
            except Exception as e:
                logger.warning(f"Failed to read photo: {e}")
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
            threading.Thread(target=_send_sync, args=(url, payload), daemon=True).start()


# ── Wake-lock script (shared across all pages) ────────────
_WAKELOCK_HTML = """
<script>
let wakeLock = null;
const requestWakeLock = async () => { try { wakeLock = await navigator.wakeLock.request('screen'); } catch (err) { console.log(`${err.name}, ${err.message}`); } };
requestWakeLock();
document.addEventListener('visibilitychange', async () => { if (wakeLock !== null && document.visibilityState === 'visible') { requestWakeLock(); } });
</script>
"""

def render_wakelock():
    st.markdown(_WAKELOCK_HTML, unsafe_allow_html=True)


# ── Session-state bulk initializer ────────────────────────
def init_session_state(**defaults):
    """Set multiple session_state keys only if they don't already exist.
    Usage: init_session_state(is_bot_running=False, np_df=None, ...)
    """
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _load_css(filename: str) -> str:
    path = os.path.join("static", filename)
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def inject_css(filename: str = "style.css"):
    css = _load_css(filename)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def clean_html(html_str: str) -> str:
    """Removes leading/trailing whitespace from each line and joins them into a single line to prevent Streamlit/Markdown code block rendering bugs."""
    if not html_str:
        return ""
    return " ".join(line.strip() for line in html_str.splitlines())

def _make_alert_box(text: str, bg_color: str, text_color: str, svg_path: str, border_left: str = "2px solid transparent") -> str:
    return clean_html(f"""
        <div style='
            background-color: {bg_color};
            color: {text_color};
            height: 38.4px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 0px;
            font-weight: 800;
            font-size: 0.85rem;
            margin-top: 16px;
            margin-bottom: 24px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: "Source Sans 3", "Source Sans Pro", sans-serif;
            border: 2px solid #0F172A;
            border: 3px solid #0F172A; border-radius: 0px;
            width: 100%;
            box-sizing: border-box;
            box-shadow: 6px 6px 0px 0px #0F172A;
        '>
            <svg xmlns="http://www.w3.org/2000/svg" height="20" viewBox="0 -960 960 960" width="20" fill="currentColor" style="margin-right: 8px;">
                <path d="{svg_path}"/>
            </svg>
            {html.escape(str(text))}
        </div>
    """)

def make_solid_box(text: str, border_color: str, text_color: str) -> str:
    bg = border_color
    fg = "#FFFFFF" if text_color == border_color else text_color
    return _make_alert_box(text, bg, fg, "M440-280h80v-240h-80v240Zm40-320q17 0 28.5-11.5T520-640q0-17-11.5-28.5T480-680q-17 0-28.5 11.5T440-640q0 17 11.5 28.5T480-600Zm0 520q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z", f"8px solid {border_color}")

def make_success_box(text: str) -> str:
    return _make_alert_box(text, "#2E7D32", "#FFFFFF", "m424-296 282-282-56-56-226 226-114-114-56 56 170 170Zm56 216q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z", "8px solid #2E7D32")

def make_error_box(text: str) -> str:
    return _make_alert_box(text, "#FFFFFF", "#D32F2F", "M480-280q17 0 28.5-11.5T520-320q0-17-11.5-28.5T480-360q-17 0-28.5 11.5T440-320q0 17 11.5 28.5T480-280Zm-40-160h80v-320h-80v320Zm40 360q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z", "8px solid #D32F2F")

def render_metric_card(title, value, accent=False):
    # Neo-Brutalist Premium Execution style for metric cards
    bg = "#0068C9" if accent else "#FFFFFF"
    fg = "#FFFFFF" if accent else "#0F172A"
    border = "3px solid #0F172A"
    shadow = "6px 6px 0px 0px #0F172A"
    
    title = html.escape(str(title))
    value_str = html.escape(str(value))
    
    # Dynamic font sizing and centering calculations
    if len(value_str) > 20:
        font_size_px = 18
    elif len(value_str) > 10:
        font_size_px = 24
    else:
        font_size_px = 38
        
    font_size = f"{font_size_px}px"
    
    return clean_html(f"""
    <div style='
        background-color: {bg};
        color: {fg};
        border: {border};
        border-radius: 0px;
        padding: 20px 24px;
        width: 100%;
        height: 125px;
        box-sizing: border-box;
        font-family: "Source Sans 3", "Source Sans Pro", sans-serif;
        margin-bottom: 16px;
        box-shadow: {shadow};
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 12px;
    '>
        <div style='font-size: 10px; font-weight: 800; color: #0F172A; background-color: {"#FFDE59" if accent else "#FFFFFF"}; border: 2px solid #0F172A; box-shadow: 2px 2px 0px 0px #0F172A; padding: 4px 10px; text-transform: uppercase; letter-spacing: 0.08em; line-height: 1; display: inline-block;'>{title}</div>
        <div style='font-size: {font_size}; font-weight: 900; color: {fg}; line-height: 1;'>{value_str}</div>
    </div>
    """)

def render_terminal(placeholder, logs_history: list):
    display_logs = "<br>".join(logs_history[-100:])
    html_content = f"""
    <div style="position: relative; margin-top: 0px; margin-bottom: -12px;">
        <div class="terminal-box" id="ext_term_box">{display_logs}<br><span class="blink_me">&#9608;</span></div>
    </div>
    <script>
        var t = window.parent.document.getElementById('ext_term_box') || document.getElementById('ext_term_box');
        if (t) t.scrollTop = t.scrollHeight;
    </script>
    """
    placeholder.markdown(html_content, unsafe_allow_html=True)

def check_auth():
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("Silakan login di halaman utama terlebih dahulu.")
        st.stop()
    if "current_user" not in st.session_state:
        st.session_state.current_user = "Guest"

def render_indicators(db_status, bot_status, bot_type="ENGINE"):
    db_color = "#0068C9" if db_status == "CONNECTED" else "#FF2B2B"
    bot_color = "#31333F" if "PROMO" not in bot_type else "#0068C9"
    
    user_pill = ""
    if "current_user" in st.session_state and st.session_state.current_user:
        user_pill = f"""
            <div style='margin-left: auto; pointer-events: none; display: inline-flex; align-items: center; background: #FFFFFF; border: 2px solid #0F172A; box-shadow: 3px 3px 0px 0px #0F172A; padding: 4px 12px; gap: 6px;'>
                <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.7rem; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.05em;'>SESSION:</span>
                <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.7rem; font-weight: 900; color: #0068C9; text-transform: uppercase; letter-spacing: 0.05em;'>{html.escape(str(st.session_state.current_user))}</span>
            </div>
        """
        
    indicator_html = clean_html(f"""
        <div style='display: flex; gap: 10px; margin-bottom: 16px; align-items: center;'>
            <div class='live-indicator'>LIVE</div>
            {user_pill}
        </div>
    """)
    st.markdown(indicator_html, unsafe_allow_html=True)

def render_header(title, subtitle=""):
    inject_css()  # uses cached CSS, no repeated file I/O
    html_out = ""

    if "Automation Tool" not in title:
        st.page_link("pages/0_dashboard.py", label="Dashboard", icon=":material/home:")
        
        MODULE_META = {
            "Inventory Adjustment": {"desc": "Singkronisasi & rekonsiliasi data stok fisik vs sistem", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'></path><polyline points='3.27 6.96 12 12.01 20.73 6.96'></polyline><line x1='12' y1='22.08' x2='12' y2='12'></line></svg>", "color": "#FFDE59"},
            "Sales Extraction": {"desc": "Otomatisasi penarikan faktur penjualan distributor", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='3' width='20' height='14' rx='2' ry='2'></rect><line x1='8' y1='21' x2='16' y2='21'></line><line x1='12' y1='17' x2='12' y2='21'></line></svg>", "color": "#4CC9F0"},
            "Sales Data Extraction": {"desc": "Otomatisasi penarikan faktur penjualan distributor", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='3' width='20' height='14' rx='2' ry='2'></rect><line x1='8' y1='21' x2='16' y2='21'></line><line x1='12' y1='17' x2='12' y2='21'></line></svg>", "color": "#4CC9F0"},
            "Promotion Comparison": {"desc": "Audit & komparasi data klaim promosi berjalan", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'></path><polyline points='14 2 14 8 20 8'></polyline><line x1='16' y1='13' x2='8' y2='13'></line><line x1='16' y1='17' x2='8' y2='17'></line><polyline points='10 9 9 9 8 9'></polyline></svg>", "color": "#FF90E8"},
            "Stock Mutation": {"desc": "Lacak riwayat pergerakan stok harian (masuk/keluar)", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'></circle><polyline points='12 16 16 12 12 8'></polyline><line x1='8' y1='12' x2='16' y2='12'></line></svg>", "color": "#4ADE80"},
            "Mutasi Stock": {"desc": "Lacak riwayat pergerakan stok harian (masuk/keluar)", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'></circle><polyline points='12 16 16 12 12 8'></polyline><line x1='8' y1='12' x2='16' y2='12'></line></svg>", "color": "#4ADE80"},
            "Clearance Stock": {"desc": "Monitor barang clearance dan sisa stok mati", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'></circle><line x1='15' y1='9' x2='9' y2='15'></line><line x1='9' y1='9' x2='15' y2='15'></line></svg>", "color": "#FF9F1C"},
            "Initial Stock": {"desc": "Setup baseline data stok awal untuk distributor baru", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='18' height='18' rx='2' ry='2'></rect><line x1='12' y1='8' x2='12' y2='16'></line><line x1='8' y1='12' x2='16' y2='12'></line></svg>", "color": "#A78BFA"},
            "Element Crawler": {"desc": "Otomatisasi ekstraksi ID & Selector elemen web", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='3'></circle><path d='M3 12h5'></path><path d='M16 12h5'></path><path d='M12 3v5'></path><path d='M12 16v5'></path><path d='M5.636 5.636l3.536 3.536'></path><path d='M14.828 14.828l3.536 3.536'></path><path d='M5.636 18.364l3.536-3.536'></path><path d='M14.828 9.172l3.536-3.536'></path></svg>", "color": "#F87171"}
        }
        
        meta = MODULE_META.get(title, {"desc": "Modul otomatisasi distributor", "icon": "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2'></polygon></svg>", "color": "#FFDE59"})
        desc, icon, bg_color = meta["desc"], meta["icon"], meta.get("color", "#FFDE59")
        
        html_out += f"""
        <div style='margin-bottom: 0px; padding: clamp(16px, 3vw, 24px); background: #FFFFFF; border: 3px solid #0F172A; border-radius: 0px; box-shadow: 6px 6px 0px 0px #0F172A; display: flex; flex-wrap: wrap; align-items: center; gap: 20px;'>
            <div style='font-size: 2.2rem; background: {bg_color}; border: 3px solid #0F172A; border-radius: 0px; min-width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; box-shadow: 4px 4px 0px 0px #0F172A; color: #0F172A;'>
                {icon}
            </div>
            <div style='flex: 1; min-width: 200px;'>
                <div style='margin: 0; font-size: clamp(1.4rem, 4vw, 1.8rem); font-weight: 800; color: #0F172A; line-height: 1.1; padding: 0; letter-spacing: -0.02em; word-wrap: break-word;'>{title}</div>
                <div style='margin: 6px 0 0 0; font-size: clamp(0.75rem, 2vw, 0.95rem); color: #334155; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>{desc}</div>
            </div>
        </div>
        """
        
        flat_toggle_css = """
        <style>
        /* THE ULTIMATE FLAT PREMIUM TOGGLE CARD (Neo-Brutalism / Modern Enterprise) */
        div.element-container:has(.dry-run-anchor) + div.element-container {
            background-color: #FFFFFF;
            border: 3px solid #0F172A;
            border-radius: 0px;
            padding: 20px 24px;
            margin-top: 16px;
            margin-bottom: 0px;
            width: 100%;
            box-shadow: 6px 6px 0px 0px #0F172A; /* Solid flat shadow, NO blur */
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }
        
        div.element-container:has(.dry-run-anchor) + div.element-container:hover {
            
            
            border-color: #0F172A;
        }
        
        /* Make the label take full width and flip order (toggle on right, text on left) */
        div.element-container:has(.dry-run-anchor) + div.element-container label {
            display: flex !important;
            flex-direction: row-reverse !important;
            justify-content: space-between !important;
            align-items: center !important;
            width: 100% !important;
            cursor: pointer;
            min-height: max-content !important;
            height: auto !important;
            padding-bottom: 4px !important;
        }

        div.element-container:has(.dry-run-anchor) + div.element-container label p {
            font-size: 1.15rem !important;
            font-weight: 900 !important;
            color: #0F172A !important;
            margin: 0 !important;
            letter-spacing: -0.01em;
            display: flex;
            flex-direction: column;
            text-transform: uppercase;
        }
        
        /* Inject a beautiful subtitle directly into the UI without needing tooltips */
        div.element-container:has(.dry-run-anchor) + div.element-container label p::after {
            content: "Execution simulator is active. Bots will run normally but final Save/Download actions to the database will be explicitly bypassed for safety.";
            display: inline-block;
            font-family: "Courier New", Courier, monospace;
            font-size: 0.8rem;
            font-weight: 700;
            color: #0F172A;
            background: #F1F5F9;
            padding: 6px 10px;
            border: 2px solid #0F172A;
            margin-top: 10px;
            line-height: 1.4;
            max-width: 90%;
            white-space: normal;
            box-shadow: 3px 3px 0px 0px #0F172A;
            text-transform: none;
        }
        </style>
        <div class="dry-run-anchor" style="display: none;"></div>
        """
        st.markdown(html_out + flat_toggle_css, unsafe_allow_html=True)
        st.toggle("SECURITY MODE: DRY RUN (SIMULATE ONLY)", key="dry_run_enabled")
    else:
        st.markdown(html_out, unsafe_allow_html=True)

def render_footer():
    st.markdown(clean_html("""
    <div style='text-align: center; margin-top: 80px; margin-bottom: 20px;'>
        <div>
            <span style='font-size: 0.85rem; font-weight: 600; color: #0F172A; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>
                &copy; 2026 IT Support Newspage.
            </span>
            <span style='font-size: 0.85rem; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>
                by kopi mang toni.
            </span>
        </div>
        <div style='background-color: #FFFFFF; border: 3px solid #0F172A; box-shadow: 6px 6px 0px 0px #0F172A; border-radius: 0px; padding: 16px 24px; font-size: 0.9rem; color: #5D6271; margin-top: 18px; max-width: 680px; margin-left: auto; margin-right: auto; line-height: 1.6; text-align: center;'>
            <strong style="color: #0F172A; display: block; margin-bottom: 8px; text-transform: uppercase; font-size: 1rem; letter-spacing: 0.05em;">Disclaimer</strong>
            This application is an independently developed by Muhammad Rizki Firdaus (Contractor), unofficial utility designed solely to automate repetitive tasks, improve operational efficiency, and save working hours. It is not officially endorsed, sponsored, or affiliated with Reckitt, Accenture, or the Newspage platform.
        </div>
    </div>
    """), unsafe_allow_html=True)



def make_terminal_logger(placeholder):
    import time
    from datetime import datetime, timezone, timedelta
    
    logs_history = []
    last_log_time = [time.time()]

    def ui_log(module, msg):
        now = time.time()
        diff_ms = int((now - last_log_time[0]) * 1000)
        last_log_time[0] = now
        timestamp = datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')
        tag_class = f"tag-{module.lower()}"
        logs_history.append(f"<span class='log-time'>[{timestamp}]</span><span class='log-ms'>[+{diff_ms}ms]</span><span class='log-tag {tag_class}'>{module}</span><span class='log-msg'>{html.escape(str(msg))}</span>")
        render_terminal(placeholder, logs_history)

    return ui_log, logs_history

def resolve_distributor_url(list_dist):
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
    return url_dist, default_index

def resolve_date_url():
    import datetime
    from datetime import timezone, timedelta
    today_jakarta = datetime.datetime.now(timezone(timedelta(hours=7))).date()
    sd, ed = today_jakarta.replace(day=1), today_jakarta
    
    def parse_dt(keys):
        for k in keys:
            if val := st.query_params.pop(k, None) if k in ("start_date", "end_date") else st.query_params.get(k):
                try: return datetime.datetime.strptime(decode_param(val) if k in ("sd", "ed") else val, "%Y-%m-%d").date()
                except: pass
        return None

    return parse_dt(("sd", "start_date")) or sd, parse_dt(("ed", "end_date")) or ed


def safe_parse_numeric(val) -> float:
    if val is None: return 0.0
    if isinstance(val, (int, float)):
        import math
        return float(val) if not math.isnan(val) else 0.0
    s = str(val).strip().replace(' ', '')
    if not s or s.lower() in ('nan', 'none'): return 0.0
    if s.endswith('-'): s = '-' + s[:-1]
    
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.') if s.rfind(',') > s.rfind('.') else s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '') if len(s.split(',')[-1]) == 3 else s.replace(',', '.')
    elif '.' in s:
        s = s.replace('.', '') if s.count('.') > 1 or len(s.split('.')[-1]) == 3 else s
    
    try: return float(s)
    except ValueError: return 0.0



def render_neo_table(df_or_placeholder, df=None):
    """
    Renders a neo-brutalist table.
    Can be called as render_neo_table(df) or render_neo_table(placeholder, df)
    """
    import pandas as pd
    if df is None:
        target_df = df_or_placeholder
        target = st
    else:
        target_df = df
        target = df_or_placeholder
        
    if not isinstance(target_df, pd.DataFrame):
        target_df = pd.DataFrame(target_df)
        
    html = target_df.to_html(
        index=False, 
        classes="neo-table", 
        escape=True,
        float_format=lambda x: str(int(x)) if x.is_integer() else str(x)
    )
    html_str = f'<div class="neo-table-wrapper">{html}</div>'
    target.markdown(html_str, unsafe_allow_html=True)


def render_responsive_dataframe(df_or_placeholder, df=None):
    """
    Renders a dataframe that shows as a neo-brutalist table on desktop
    and stacks into mobile cards on screens < 768px.
    """
    import pandas as pd
    
    if df is None:
        target_df = df_or_placeholder
        target = st
    else:
        target_df = df
        target = df_or_placeholder
        
    if not isinstance(target_df, pd.DataFrame):
        target_df = pd.DataFrame(target_df)

    # 1. Desktop Table HTML
    desktop_html = target_df.to_html(
        index=False, 
        classes="neo-table", 
        escape=True,
        float_format=lambda x: str(int(x)) if x.is_integer() else str(x)
    )
    desktop_div = f'<div class="desktop-only-table"><div class="neo-table-wrapper">{desktop_html}</div></div>'
    
    # 2. Mobile Cards HTML
    cards_html = []
    for _, row in target_df.iterrows():
        cards_html.append('<div class="mobile-data-card">')
        for col_name, val in row.items():
            str_val = str(int(val)) if isinstance(val, float) and val.is_integer() else str(val)
            cards_html.append(f'''
            <div class="mobile-data-row">
                <span class="mobile-data-label">{html.escape(str(col_name))}</span>
                <span class="mobile-data-value">{html.escape(str_val)}</span>
            </div>
            ''')
        cards_html.append('</div>')
    
    mobile_div = f'<div class="mobile-only-cards">{"".join(cards_html)}</div>'
    
    # 3. Combine and render
    target.markdown(desktop_div + mobile_div, unsafe_allow_html=True)
