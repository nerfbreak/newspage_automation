"""Database module - framework-agnostic version for Reflex migration.
Uses environment variables instead of st.secrets, no @st.cache_resource.
"""
import os
import logging
import bcrypt
from cryptography.fernet import Fernet
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# ============================================================
# Singleton Supabase client (replaces @st.cache_resource)
# ============================================================
_supabase_client: Client | None = None

def init_supabase() -> Client | None:
    """Backwards-compatible: still tries st.secrets first, falls back to env vars."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            _supabase_client = create_client(url, key)
            return _supabase_client
    except Exception:
        pass
    # Fallback to env vars (for Reflex)
    return init_supabase_direct()


def init_supabase_direct() -> Client | None:
    """Pure env-var version for Reflex (no Streamlit dependency)."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if url and key:
        _supabase_client = create_client(url, key)
        return _supabase_client
    return None


def get_encryption_key():
    """Try st.secrets first, then env var."""
    try:
        import streamlit as st
        key = st.secrets.get("MASTER_KEY", "")
        if key:
            return key.encode()
    except Exception:
        pass
    key = os.environ.get("MASTER_KEY", "")
    if not key:
        raise ValueError("MASTER_KEY not found in secrets or environment.")
    return key.encode()

def encrypt_data(data: str) -> str:
    if not data: return ""
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    if not encrypted_data: return ""
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logging.error(f"Decryption error: {e}")
        return ""  # Return empty string instead of ciphertext to prevent silent data corruption

import streamlit as st

@st.cache_data(ttl=300)
def get_system_config(_supabase):
    """Fetch system config with Streamlit thread-safe caching.
    Returns a dict with keys: REASON_CODE, WAREHOUSE, URL_LOGIN, TIMEOUT_MS, TABLE_UPDATE_INTERVAL.
    """
    supabase = _supabase

    cfg = {
        "REASON_CODE": "SA2",
        "WAREHOUSE": "GOOD_WHS",
        "URL_LOGIN": "",
        "TIMEOUT_MS": 60_000,
        "TABLE_UPDATE_INTERVAL": 5,
    }
    if supabase:
        try:
            res_config = supabase.table("system_config").select("*").execute()
            for row in res_config.data:
                key = row["config_key"]
                val = row["config_value"]
                if key in cfg:
                    # Cast numeric strings to int
                    if key in ("TIMEOUT_MS", "TABLE_UPDATE_INTERVAL"):
                        try:
                            cfg[key] = int(val)
                        except ValueError:
                            pass
                    else:
                        cfg[key] = val
        except Exception as e:
            logging.error(f"Error fetching system_config: {e}")

    return cfg

def authenticate_user(supabase, username, password):
    if supabase:
        try:
            res_user = supabase.table("users_auth").select("password").eq("username", username).execute()
            if res_user.data:
                hashed_pw = res_user.data[0]['password'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
                    return True
        except Exception as e:
            logging.error(f"Error authenticating user {username}: {e}")
    return False

@st.cache_data(ttl=300)
def get_distributor_list(_supabase):
    """Fetch distributor list with thread-safe caching."""
    supabase = _supabase
    
    list_dist = []
    if supabase:
        try:
            res = supabase.table("distributor_vault").select("nama_distributor").execute()
            list_dist = [d['nama_distributor'] for d in res.data]
        except Exception as e:
            logging.error(f"Error fetching distributor list: {e}")
    if not list_dist: list_dist = ["Belum ada data di Database"]
    
    return list_dist

def get_distributor_creds(supabase, selected_distributor):
    bot_user, bot_pass = "", ""
    if supabase:
        try:
            res = supabase.table("distributor_vault").select("np_user_id, np_password").eq("nama_distributor", selected_distributor).execute()
            if res.data:
                bot_user = res.data[0]['np_user_id']
                # Decrypt the password for engine use
                bot_pass = decrypt_data(res.data[0]['np_password'])
        except Exception as e:
            logging.error(f"Error fetching distributor creds for {selected_distributor}: {e}")
    return bot_user, bot_pass

def get_target_skus(supabase):
    TARGET_SKUS = []
    if supabase:
        try:
            res_sku = supabase.table("sku_formatting_rules").select("sku_code").execute()
            TARGET_SKUS = [s['sku_code'] for s in res_sku.data]
        except Exception as e:
            logging.error(f"Error fetching target skus: {e}")
    if not TARGET_SKUS: 
        TARGET_SKUS = ['373103', '373104', '373105', '373106', '373108', '373110', '373112', '135428', '137118', '137120', '167209', '172130', '172131', '205901', '22583', '22595', '260656', '260659', '304095', '304100', '304102', '304157', '304161', '304164', '323044', '372264', '373100']
    return TARGET_SKUS

def get_multiplier_rules(supabase, current_np_user_id):
    rules = []
    if supabase and current_np_user_id:
        try:
            res_mult = supabase.table("distributor_sku_multiplier").select("sku_target, multiplier_value").eq("np_user_id", current_np_user_id).execute()
            if res_mult.data:
                rules = res_mult.data
        except Exception as e:
            logging.error(f"Error fetching multiplier rules for {current_np_user_id}: {e}")
    return rules

def log_extraction_history(supabase, selected_distributor, current_user):
    if supabase:
        try:
            supabase.table("extraction_history").insert({
                "distributor_name": selected_distributor,
                "extracted_by": current_user,
                "status": "Success"
            }).execute()
        except Exception as e:
            logging.error(f"Error logging extraction history for {selected_distributor}: {e}")

def log_adjustment(supabase, sku, qty, status, keterangan, bot_user):
    if supabase:
        try:
            # Cegah error integer kalau timeout dan node kosong
            safe_qty = int(qty) if str(qty).replace('-','').isdigit() else 0
            supabase.table("adjustment_logs").insert({
                "sku": sku, "qty": safe_qty, "status": status, 
                "keterangan": keterangan, "np_user": bot_user
            }).execute()
        except Exception as e:
            logging.error(f"Error logging adjustment for SKU {sku}: {e}")


def get_secret(key: str, default: str = "") -> str:
    """Retrieve a secret from st.secrets (Streamlit) or os.environ (Reflex)."""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(key, default)

def get_distributor_warehouse_exceptions(supabase):
    """
    Returns a dictionary of distributor_id -> target_warehouse.
    """
    exceptions = {}
    if supabase:
        try:
            res = supabase.table("distributor_exceptions").select("distributor_id, target_warehouse").execute()
            if res.data:
                for row in res.data:
                    exceptions[row['distributor_id']] = row['target_warehouse']
        except Exception as e:
            logging.error(f"Error fetching distributor_exceptions: {e}")
    return exceptions

# ============================================================
# Security: Brute Force Protection
# ============================================================
def check_login_lockout(supabase, username):
    """Returns (is_locked: bool, remaining_seconds: int, attempts: int)"""
    if not supabase: return False, 0, 0
    try:
        res = supabase.table("login_attempts").select("attempts, lockout_until").eq("username", username).execute()
        if not res.data:
            return False, 0, 0
            
        attempts = res.data[0].get('attempts', 0)
        lockout_until_str = res.data[0].get('lockout_until')
        
        if lockout_until_str:
            from datetime import datetime
            import time
            lockout_time = datetime.fromisoformat(lockout_until_str.replace('Z', '+00:00')).timestamp()
            now = time.time()
            if now < lockout_time:
                return True, int(lockout_time - now), attempts
            else:
                reset_failed_login(supabase, username)
                return False, 0, 0
        return False, 0, attempts
    except Exception as e:
        logging.error(f"Error checking lockout: {e}")
        return False, 0, 0

def record_failed_login(supabase, username, max_attempts=5, lockout_minutes=5):
    if not supabase: return
    try:
        from datetime import datetime, timezone, timedelta
        res = supabase.table("login_attempts").select("attempts").eq("username", username).execute()
        
        attempts = 1
        if res.data:
            attempts = res.data[0].get('attempts', 0) + 1
            
        data = {"username": username, "attempts": attempts, "last_attempt": datetime.now(timezone.utc).isoformat()}
        
        if attempts >= max_attempts:
            lockout_time = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)
            data["lockout_until"] = lockout_time.isoformat()
            
        supabase.table("login_attempts").upsert(data).execute()
    except Exception as e:
        logging.error(f"Error recording failed login: {e}")

def reset_failed_login(supabase, username):
    if not supabase: return
    try:
        from datetime import datetime, timezone
        supabase.table("login_attempts").upsert({
            "username": username,
            "attempts": 0,
            "lockout_until": None,
            "last_attempt": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        logging.error(f"Error resetting failed login: {e}")

