"""Database module for Supabase operations.
Handles auth, encryption, system config, and distributor vault.
"""
import os
import time
import logging
import json
import uuid
import bcrypt
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# SKU prefixes to exclude from stock operations (e.g., non-inventory items)
EXCLUDE_PREFIX = ['8021803', '8021804']

# ============================================================
# Singleton Supabase client (replaces @st.cache_resource)
# ============================================================
_supabase_client: Client | None = None

def init_supabase() -> Client | None:
    """Returns singleton Supabase client. Tries st.secrets first, falls back to env vars."""
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
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if url and key:
        _supabase_client = create_client(url, key)
    return _supabase_client


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

def get_user_session_version(supabase, username):
    """Return the current remembered-session version for a user."""
    if not supabase or not username:
        return ""
    try:
        res = supabase.table("users_auth").select("session_version").eq("username", username).execute()
        if res.data:
            return str(res.data[0].get("session_version") or "")
    except Exception as e:
        logging.error(f"Error fetching session version for user {username}: {e}")
    return ""

def ensure_user_session_version(supabase, username):
    """Ensure a user has a non-secret session version for remembered-login cookies."""
    current_version = get_user_session_version(supabase, username)
    if current_version:
        return current_version
    if not supabase or not username:
        return ""
    try:
        new_version = uuid.uuid4().hex
        supabase.table("users_auth").update({
            "session_version": new_version,
            "password_changed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("username", username).execute()
        persisted_version = get_user_session_version(supabase, username)
        if persisted_version == new_version:
            return persisted_version
    except Exception as e:
        logging.error(f"Error ensuring session version for user {username}: {e}")
    return ""

def create_remembered_session_payload(username, session_version, server_run_id):
    """Create an encrypted structured remembered-session payload."""
    if not username or not session_version or not server_run_id:
        return ""
    payload = json.dumps(
        {"username": username, "session_version": session_version, "server_run_id": server_run_id},
        separators=(",", ":"),
    )
    return encrypt_data(payload)

def parse_remembered_session_payload(encrypted_payload):
    """Decrypt and parse a remembered-session cookie payload."""
    decrypted = decrypt_data(encrypted_payload)
    if not decrypted:
        return {}
    try:
        payload = json.loads(decrypted)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    username = str(payload.get("username") or "")
    session_version = str(payload.get("session_version") or "")
    server_run_id = str(payload.get("server_run_id") or "")
    if not username or not session_version or not server_run_id:
        return {}
    return {"username": username, "session_version": session_version, "server_run_id": server_run_id}

def validate_remembered_session(supabase, encrypted_payload, current_server_run_id):
    """Return username only when the remembered session matches current user metadata and server run ID."""
    payload = parse_remembered_session_payload(encrypted_payload)
    if not payload:
        return ""
    if payload.get("server_run_id") != current_server_run_id:
        return ""
    current_version = get_user_session_version(supabase, payload["username"])
    if current_version and current_version == payload["session_version"]:
        return payload["username"]
    return ""

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
                raw_password = res.data[0]['np_password']
                if raw_password:
                    # Try to decrypt
                    bot_pass = decrypt_data(raw_password)
                    if not bot_pass:
                        # Decryption failed. Check if it's plain text (does not start with Fernet prefix 'gAAAA')
                        if not raw_password.startswith("gAAAA"):
                            try:
                                # Auto-encrypt plain text password and update in Supabase
                                encrypted_pw = encrypt_data(raw_password)
                                supabase.table("distributor_vault").update({"np_password": encrypted_pw}).eq("nama_distributor", selected_distributor).execute()
                                bot_pass = raw_password
                                logging.info(f"Auto-encrypted plain text password for distributor: {selected_distributor}")
                            except Exception as enc_err:
                                logging.error(f"Failed to auto-encrypt password for {selected_distributor}: {enc_err}")
                                bot_pass = raw_password  # Fallback to plain text for this run
                        else:
                            logging.error(f"Password for {selected_distributor} appears to be encrypted with a different key.")
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

def log_extraction_history(supabase, selected_distributor, current_user, status="Success"):
    if supabase:
        try:
            supabase.table("extraction_history").insert({
                "distributor_name": selected_distributor,
                "extracted_by": current_user,
                "status": status
            }).execute()
        except Exception as e:
            logging.error(f"Error logging extraction history for {selected_distributor}: {e}")

def log_adjustment(supabase, sku, qty, status, keterangan, bot_user, run_by=None):
    if supabase:
        try:
            try: safe_qty = int(float(qty))
            except (ValueError, TypeError): safe_qty = 0
            payload = {
                "sku": sku, "qty": safe_qty, "status": status,
                "keterangan": keterangan, "np_user": bot_user
            }
            if run_by:
                payload["run_by"] = run_by
            supabase.table("adjustment_logs").insert(payload).execute()
        except Exception as e:
            logging.error(f"Error logging adjustment for SKU {sku}: {e}")


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
        supabase.table("login_attempts").upsert({
            "username": username,
            "attempts": 0,
            "lockout_until": None,
            "last_attempt": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        logging.error(f"Error resetting failed login: {e}")

