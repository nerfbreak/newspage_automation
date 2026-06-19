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
    # Dark card surface (#262626) and border (#404040)
    return clean_html(f"""
        <div style='
            background-color: #262626;
            color: {text_color};
            height: 38.4px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            border: 1px solid #404040;
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
    # Primary blue (#3b82f6) background with light text
    return clean_html(f"""
        <div style='
            background-color: #3b82f6;
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
    db_color = "#3b82f6" if db_status == "CONNECTED" else "#ef4444"
    bot_color = "#e5e5e5" if "PROMO" not in bot_type else "#3b82f6"
    
    html = clean_html(f"""
        <div style='display: flex; gap: 10px; margin-bottom: 16px; align-items: center;'>
            <div class='live-indicator'>LIVE</div>
            <div class='status-pill' style='color: {db_color}; border-color: {db_color}33; background-color: {db_color}1a;'>
                DB: {db_status}
            </div>
            <div class='status-pill' style='color: {bot_color}; border-color: {bot_color}33; background-color: {bot_color}1a;'>
                {bot_type}: {bot_status}
            </div>
        </div>
    """)
    st.markdown(html, unsafe_allow_html=True)

def render_header(title, subtitle=""):
    inject_css()  # uses cached CSS, no repeated file I/O

    if "Automation Tool" not in title:
        back_key = f"btn_back_to_dash_{title.lower().replace(' ', '_')}"
        if st.button("Dashboard", key=back_key, type="primary"):
            st.switch_page("pages/0_dashboard.py")
        st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(clean_html(f"""
            <div style='display: inline-block; margin-top: -4px;'>
                <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 0.65rem; font-weight: 700; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.1em; margin-right: 8px;'>Active Session</span>
                <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 0.65rem; font-weight: 700; color: #e5e5e5; text-transform: uppercase; letter-spacing: 0.1em;'>{subtitle}</span>
            </div>
        """), unsafe_allow_html=True)

def render_footer():
    st.markdown(clean_html("""
    <div style='text-align: center; margin-top: 80px; margin-bottom: 20px;'>
        <span style='font-family: "Source Sans 3", "Source Sans Pro", sans-serif; font-size: 0.6rem; color: #3b82f6; letter-spacing: 0.05em; text-transform: uppercase;'>
            &copy; 2026 IT Support Newspage.
        </span>
    </div>
    """), unsafe_allow_html=True)


def style_status(df):
    """Apply color-coded styling to the Status column.
    Success = green, Failed/Error = red, Pending = yellow.
    Returns a pandas Styler object.
    """
    def _color_status(val):
        v = str(val).strip().lower()
        if v == 'success':
            return 'color: #4ade80; font-weight: 600;'
        elif v in ('failed', 'error'):
            return 'color: #f87171; font-weight: 600;'
        elif v == 'pending':
            return 'color: #facc15; font-weight: 600;'
        return ''

    if 'Status' not in df.columns:
        return df.style
    return df.style.map(_color_status, subset=['Status'])

