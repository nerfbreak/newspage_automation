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
def _send_sync(url, payload, files=None):
    try:
        if files:
            requests.post(url, data=payload, files=files, timeout=15)
        else:
            requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.warning(f"Telegram alert failed: {e}")

def send_telegram_alert(message: str, photo_path: str = None):
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
                threading.Thread(target=_send_sync, args=(url, payload, files), daemon=True).start()
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

def _make_alert_box(text: str, bg_color: str, text_color: str, svg_path: str, border_left: str = "1px solid transparent") -> str:
    return clean_html(f"""
        <div style='
            background-color: {bg_color};
            color: {text_color};
            height: 38.4px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.85rem;
            margin-top: 12px;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: "Source Sans 3", "Source Sans Pro", sans-serif;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-left: {border_left};
            width: 100%;
            box-sizing: border-box;
        '>
            <svg xmlns="http://www.w3.org/2000/svg" height="20" viewBox="0 -960 960 960" width="20" fill="currentColor" style="margin-right: 8px;">
                <path d="{svg_path}"/>
            </svg>
            {html.escape(str(text))}
        </div>
    """)

def make_solid_box(text: str, border_color: str, text_color: str) -> str:
    return _make_alert_box(text, "#F0F2F6", text_color, "M440-280h80v-240h-80v240Zm40-320q17 0 28.5-11.5T520-640q0-17-11.5-28.5T480-680q-17 0-28.5 11.5T440-640q0 17 11.5 28.5T480-600Zm0 520q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z", f"5px solid {border_color}")

def make_success_box(text: str) -> str:
    return _make_alert_box(text, "#0068C9", "#FAFAFA", "m424-296 282-282-56-56-226 226-114-114-56 56 170 170Zm56 216q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z")

def make_error_box(text: str) -> str:
    return _make_alert_box(text, "#FF2B2B", "#FAFAFA", "M480-280q17 0 28.5-11.5T520-320q0-17-11.5-28.5T480-360q-17 0-28.5 11.5T440-320q0 17 11.5 28.5T480-280Zm-40-160h80v-320h-80v320Zm40 360q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z")

def render_metric_card(title, value, accent=False):
    # Styling variables to match Streamlit Design System theme
    bg = "#0068C9" if accent else "#F0F2F6"
    fg = "#FFFFFF" if accent else "#31333F"
    border = "1px solid rgba(0, 104, 201, 0.15)" if accent else "1px solid rgba(0, 0, 0, 0.08)"
    shadow = "0 4px 16px rgba(0, 0, 0, 0.15)" if accent else "0 4px 12px rgba(0, 0, 0, 0.03)"
    
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
        border-radius: 10px;
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
        <div style='font-size: 11px; font-weight: 600; color: {"rgba(255, 255, 255, 0.7)" if accent else "#808495"}; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1;'>{title}</div>
        <div style='font-size: {font_size}; font-weight: 700; color: {fg}; line-height: 1;'>{value_str}</div>
    </div>
    """)

def render_terminal(placeholder, logs_history: list):
    display_logs = "<br>".join(logs_history[-100:])
    html_content = f"""
    <div class="terminal-box" id="ext_term_box">{display_logs}<br><span class="blink_me">&#9608;</span></div>
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
            <div style='margin-left: auto; pointer-events: none; display: inline-flex; align-items: center; gap: 6px;'>
                <svg xmlns="http://www.w3.org/2000/svg" height="14" viewBox="0 -960 960 960" width="14" fill="#838C96"><path d="M480-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47ZM160-160v-112q0-34 17.5-62.5T224-378q62-31 126-46.5T480-440q66 0 130 15.5T736-378q29 15 46.5 43.5T800-272v112H160Zm80-80h480v-32q0-11-5.5-20T700-306q-54-27-109-40.5T480-360q-56 0-111 13.5T260-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T560-640q0-33-23.5-56.5T480-720q-33 0-56.5 23.5T400-640q0 33 23.5 56.5T480-560Zm0-80Zm0 400Z"/></svg>
                <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.65rem; font-weight: 600; color: #838C96; text-transform: uppercase; letter-spacing: 0.05em;'>Session:</span>
                <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.65rem; font-weight: 800; color: #0068C9; text-transform: uppercase; letter-spacing: 0.05em;'>{html.escape(str(st.session_state.current_user))}</span>
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

    active_sess = ""
    # Hanya tampilkan Active Session di header jika di halaman Dashboard
    if subtitle and "Automation Tool" in title:
        active_sess = f"""<div style='float: right; margin-top: 5px; pointer-events: none; display: inline-flex; align-items: center; gap: 6px;'>
            <svg xmlns="http://www.w3.org/2000/svg" height="14" viewBox="0 -960 960 960" width="14" fill="#838C96"><path d="M480-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47ZM160-160v-112q0-34 17.5-62.5T224-378q62-31 126-46.5T480-440q66 0 130 15.5T736-378q29 15 46.5 43.5T800-272v112H160Zm80-80h480v-32q0-11-5.5-20T700-306q-54-27-109-40.5T480-360q-56 0-111 13.5T260-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T560-640q0-33-23.5-56.5T480-720q-33 0-56.5 23.5T400-640q0 33 23.5 56.5T480-560Zm0-80Zm0 400Z"/></svg>
            <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.65rem; font-weight: 600; color: #838C96; text-transform: uppercase; letter-spacing: 0.05em;'>Session:</span>
            <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.65rem; font-weight: 800; color: #0068C9; text-transform: uppercase; letter-spacing: 0.05em;'>{subtitle}</span>
        </div>"""
        
    html_out = ""
    if active_sess:
        html_out += active_sess
        
    if "Automation Tool" not in title:
        st.page_link("pages/0_dashboard.py", label="Dashboard", icon=":material/home:")
        
        MODULE_META = {
            "Inventory Adjustment": {"desc": "Singkronisasi & rekonsiliasi data stok fisik vs sistem", "icon": "📦"},
            "Sales Extraction": {"desc": "Otomatisasi penarikan faktur penjualan distributor", "icon": "🖥️"},
            "Sales Data Extraction": {"desc": "Otomatisasi penarikan faktur penjualan distributor", "icon": "🖥️"},
            "Promotion Comparison": {"desc": "Audit & komparasi data klaim promosi berjalan", "icon": "📄"},
            "Stock Mutation": {"desc": "Lacak riwayat pergerakan stok harian (masuk/keluar)", "icon": "🔄"},
            "Mutasi Stock": {"desc": "Lacak riwayat pergerakan stok harian (masuk/keluar)", "icon": "🔄"},
            "Clearance Stock": {"desc": "Monitor barang clearance dan sisa stok mati", "icon": "❌"},
            "Initial Stock": {"desc": "Setup baseline data stok awal untuk distributor baru", "icon": "➕"},
            "Element Crawler": {"desc": "Otomatisasi ekstraksi ID & Selector elemen web", "icon": "🕷️"}
        }
        
        meta = MODULE_META.get(title, {"desc": "Modul otomatisasi distributor", "icon": "⚡"})
        desc, icon = meta["desc"], meta["icon"]
        
        html_out += f"""
        <div style='margin-top: 8px; margin-bottom: 24px; padding: 20px 24px; background: linear-gradient(to right, #F8FAFC, #FFFFFF); border: 1px solid #E2E8F0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); display: flex; align-items: center; gap: 16px;'>
            <div style='font-size: 2rem; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; min-width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'>
                {icon}
            </div>
            <div>
                <h1 style='margin: 0; font-size: 1.6rem; font-weight: 800; color: #0F172A; line-height: 1.2; padding: 0; border: none;'>{title}</h1>
                <p style='margin: 4px 0 0 0; font-size: 0.9rem; color: #64748B; font-weight: 500;'>{desc}</p>
            </div>
        </div>
        """
        st.markdown(html_out, unsafe_allow_html=True)
    else:
        st.markdown(html_out, unsafe_allow_html=True)
        st.markdown(f"<h1 style='font-family: \"Source Sans 3\", \"Source Sans Pro\", sans-serif; font-size: 1.75rem; font-weight: 700; color: #31333F; letter-spacing: -0.02em; margin-top: -15px; margin-bottom: -15px; padding: 0;'>{title}</h1>", unsafe_allow_html=True)

def render_footer():
    st.markdown(clean_html("""
    <div style='text-align: center; margin-top: 80px; margin-bottom: 20px;'>
        <div>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>
                &copy; 2026 IT Support Newspage.
            </span>
            <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>
                by kopi mang toni.
            </span>
        </div>
        <div style='background-color: rgba(0, 104, 201, 0.04); border: 1px solid rgba(0, 104, 201, 0.1); border-radius: 8px; padding: 12px 16px; font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 0.72rem; color: #5D6271; margin-top: 18px; max-width: 580px; margin-left: auto; margin-right: auto; line-height: 1.5; text-align: center;'>
            <strong style="color: #0068C9; display: block; margin-bottom: 4px; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em;">Disclaimer</strong>
            This application is an independently developed, unofficial utility designed solely to automate repetitive tasks, improve operational efficiency, and save working hours. It is not officially endorsed, sponsored, or affiliated with Reckitt, Accenture, or the Newspage platform.
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
        logs_history.append(f"<span class='log-time'>[{timestamp}]</span><span class='log-ms'>[+{diff_ms}ms]</span><span class='log-tag {tag_class}'>[{module}]</span><span class='log-msg'>{html.escape(str(msg))}</span>")
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


