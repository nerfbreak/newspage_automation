import os
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
def send_telegram_alert(message: str):
    bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.warning(f"Telegram alert failed: {e}")


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


# ── CSS loader (cached) ───────────────────────────────────
_CSS_CACHE: dict[str, str] = {}

def _load_css(filename: str) -> str:
    if filename not in _CSS_CACHE:
        path = os.path.join("static", filename)
        try:
            with open(path) as f:
                _CSS_CACHE[filename] = f.read()
        except FileNotFoundError:
            _CSS_CACHE[filename] = ""
    return _CSS_CACHE[filename]

def inject_css(filename: str = "style.css"):
    css = _load_css(filename)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def clean_html(html_str: str) -> str:
    """Removes leading/trailing whitespace from each line and joins them into a single line to prevent Streamlit/Markdown code block rendering bugs."""
    if not html_str:
        return ""
    return " ".join(line.strip() for line in html_str.splitlines())

def make_solid_box(text: str, border_color: str, text_color: str) -> str:
    # Use Streamlit Light Card/Surface background (#F0F2F6) and default border (rgba(0, 0, 0, 0.08))
    return clean_html(f"""
        <div style='
            background-color: #F0F2F6;
            color: {text_color};
            height: 38.4px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-left: 5px solid {border_color};
            font-weight: 600;
            font-size: 0.85rem;
            margin: 12px 0;
            width: 100%;
            box-sizing: border-box;
            font-family: "Source Sans 3", "Source Sans Pro", sans-serif;
        '>{text}</div>
    """)

def make_success_box(text: str) -> str:
    # Use Streamlit Brand Blue (#0068C9) background with Light text (#FAFAFA)
    return clean_html(f"""
        <div style='
            background-color: #0068C9;
            color: #FAFAFA;
            height: 38.4px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.85rem;
            margin-top: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: "Source Sans 3", "Source Sans Pro", sans-serif;
            border: 1px solid transparent;
            width: 100%;
            box-sizing: border-box;
        '>{text}</div>
    """)

def make_error_box(text: str) -> str:
    # Use Streamlit Brand Red (#FF2B2B) background with Light text (#FAFAFA)
    return clean_html(f"""
        <div style='
            background-color: #FF2B2B;
            color: #FAFAFA;
            height: 38.4px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.85rem;
            margin-top: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: "Source Sans 3", "Source Sans Pro", sans-serif;
            border: 1px solid transparent;
            width: 100%;
            box-sizing: border-box;
        '>{text}</div>
    """)

def render_metric_card(title, value, accent=False):
    # Styling variables to match Streamlit Design System theme
    bg = "#0068C9" if accent else "#F0F2F6"
    fg = "#FFFFFF" if accent else "#31333F"
    border = "1px solid rgba(0, 104, 201, 0.15)" if accent else "1px solid rgba(0, 0, 0, 0.08)"
    shadow = "0 4px 16px rgba(0, 0, 0, 0.15)" if accent else "0 4px 12px rgba(0, 0, 0, 0.03)"
    
    value_str = str(value)
    
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
            <div style='margin-left: auto; pointer-events: none; background-color: #f0f2f6; border: 1px solid #e0e2e6; padding: 4px 12px; border-radius: 16px; display: inline-flex; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>
                <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.65rem; font-weight: 700; color: #0068C9; text-transform: uppercase; letter-spacing: 0.05em; margin-right: 6px;'>Active Session:</span>
                <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.65rem; font-weight: 800; color: #31333F; text-transform: uppercase; letter-spacing: 0.05em;'>{st.session_state.current_user}</span>
            </div>
        """
        
    html = clean_html(f"""
        <div style='display: flex; gap: 10px; margin-bottom: 16px; align-items: center;'>
            <div class='live-indicator'>LIVE</div>
            <div class='status-pill' style='color: {db_color}; border-color: {db_color}33; background-color: {db_color}1a;'>
                DB: {db_status}
            </div>
            <div class='status-pill' style='color: {bot_color}; border-color: {bot_color}33; background-color: {bot_color}1a;'>
                {bot_type}: {bot_status}
            </div>
            {user_pill}
        </div>
    """)
    st.markdown(html, unsafe_allow_html=True)

def render_header(title, subtitle=""):
    inject_css()  # uses cached CSS, no repeated file I/O

    active_sess = ""
    # Hanya tampilkan Active Session di header jika di halaman Dashboard
    if subtitle and "Automation Tool" in title:
        active_sess = f"""<div style='float: right; margin-top: 5px; pointer-events: none; background-color: #f0f2f6; border: 1px solid #e0e2e6; padding: 4px 12px; border-radius: 16px; display: inline-flex; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>
            <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.65rem; font-weight: 700; color: #0068C9; text-transform: uppercase; letter-spacing: 0.05em; margin-right: 6px;'>Active Session:</span>
            <span style='font-family: "Source Sans 3", sans-serif; font-size: 0.65rem; font-weight: 800; color: #31333F; text-transform: uppercase; letter-spacing: 0.05em;'>{subtitle}</span>
        </div>"""
        
    if active_sess:
        st.markdown(active_sess, unsafe_allow_html=True)
        
    if "Automation Tool" not in title:
        st.markdown("""
        <style>
        /* Styling font Dashboard: Biru dan Bold */
        a[data-testid="stPageLink-NavLink"] {
            padding: 0px !important;
            margin: 0px !important;
            margin-bottom: -5px !important;
            background: transparent !important;
            border: none !important;
            text-decoration: none !important;
            width: fit-content !important;
        }
        
        a[data-testid="stPageLink-NavLink"] p {
            font-family: "Source Sans 3", sans-serif !important;
            font-size: 14px !important;
            font-weight: 800 !important;
            color: #0068C9 !important;
            margin: 0px !important;
            line-height: 1 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.page_link("pages/0_dashboard.py", label="< Back To Dashboard")
        
    st.markdown(f"<h1 style='margin-top: -5px; margin-bottom: -15px; padding-top: 0px; padding-bottom: 0px; border-bottom: none !important;'>{title}</h1>", unsafe_allow_html=True)

def render_footer():
    st.markdown(clean_html("""
    <div style='text-align: center; margin-top: 80px; margin-bottom: 20px;'>
        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #0068C9; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>
            &copy; 2026 IT Support Newspage.
        </span>
        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 10px; font-weight: 600; color: #31333F; text-transform: uppercase; letter-spacing: 0.1em;'>
            by kopi mang toni.
        </span>
    </div>
    """), unsafe_allow_html=True)


def style_status(df):
    return df

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
        logs_history.append(f"<span class='log-time'>[{timestamp}]</span><span class='log-ms'>[+{diff_ms}ms]</span><span class='log-tag {tag_class}'>[{module}]</span><span class='log-msg'>{msg}</span>")
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


def safe_parse_numeric(val) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        import math
        return float(val) if not math.isnan(val) else 0.0
    s = str(val).strip()
    if not s or s.lower() in ('nan', 'none'):
        return 0.0
    
    # Remove any spaces
    s = s.replace(' ', '')
    
    # Move minus sign from end to front (e.g. 125.00-)
    if s.endswith('-'):
        s = '-' + s[:-1]
        
    # Check for both comma and dot
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            # Indonesian format: 1.250,00 -> 1250.00
            s = s.replace('.', '').replace(',', '.')
        else:
            # English format: 1,250.00 -> 1250.00
            s = s.replace(',', '')
    elif ',' in s:
        # Only comma is present: e.g. 72,00 or 1,250
        parts = s.split(',')
        if len(parts[-1]) == 3:
            # Thousands separator: 1,250 -> 1250
            s = s.replace(',', '')
        else:
            # Decimal point: 72,00 -> 72.00
            s = s.replace(',', '.')
    elif '.' in s:
        # Only dot is present: e.g. 72.00 or 1.250
        if s.count('.') > 1:
            s = s.replace('.', '')
        else:
            parts = s.split('.')
            if len(parts[-1]) == 3:
                # Thousands separator: 1.250 -> 1250
                s = s.replace('.', '')
            else:
                # Decimal point: 72.00 -> 72.00
                pass
    try:
        return float(s)
    except ValueError:
        return 0.0

