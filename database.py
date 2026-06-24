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
# ============================================================
# Singleton Supabase client (Thread-safe)
# ============================================================

try:
    import streamlit as st
    
    @st.cache_resource
    def _get_streamlit_supabase_client():
        url = st.secrets.get("SUPABASE_URL", "") or os.environ.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
        return None

    def init_supabase() -> Client | None:
        return _get_streamlit_supabase_client()
        
except ImportError:
    _supabase_client: Client | None = None
    
    def init_supabase() -> Client | None:
        global _supabase_client
        if _supabase_client is not None:
            return _supabase_client
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if url and key:
            _supabase_client = create_client(url, key)
            return _supabase_client
        return None

def init_supabase_direct() -> Client | None:
    return init_supabase()


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

# Decorator for Streamlit cache, gracefully fallback if not in Streamlit
try:
    import streamlit as st
    cache_data_decorator = st.cache_data(ttl=600)
except ImportError:
    def cache_data_decorator(func):
        return func

@cache_data_decorator
def _fetch_system_config_internal():
    """Internal function to fetch config so we don't pass the unhashable supabase client to st.cache_data"""
    supabase = init_supabase()
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

def get_system_config(supabase=None):
    """Fetch system config with thread-safe Streamlit caching."""
    return _fetch_system_config_internal()

def authenticate_user(supabase, username, password):
    """
    Authenticates user and returns (is_authenticated, role_name).
    """
    if supabase:
        try:
            # Join with roles table to get role_name
            res_user = supabase.table("users_auth").select(
                "password, roles(role_name)"
            ).eq("username", username).execute()
            
            if res_user.data:
                user_data = res_user.data[0]
                hashed_pw = user_data['password'].encode('utf-8')
                
                if bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
                    # Extract role_name safely
                    role_name = "Operator" # Default fallback
                    if 'roles' in user_data and user_data['roles']:
                        role_name = user_data['roles'].get('role_name', 'Operator')
                    
                    return True, role_name
        except Exception as e:
            logging.error(f"Error authenticating user {username}: {e}")
            
            # Fallback for when the 'roles' table/relationship is not set up correctly yet
            # so the user is not locked out during deployment
            try:
                res_user_fallback = supabase.table("users_auth").select("password").eq("username", username).execute()
                if res_user_fallback.data:
                    hashed_pw = res_user_fallback.data[0]['password'].encode('utf-8')
                    if bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
                        logging.warning(f"Fallback auth succeeded for {username}. Role defaulting to Admin.")
                        return True, "Admin"
            except Exception as e_fallback:
                logging.error(f"Fallback auth also failed: {e_fallback}")
                
    return False, "Viewer"

@cache_data_decorator
def _fetch_distributor_list_internal():
    supabase = init_supabase()
    list_dist = []
    if supabase:
        try:
            res = supabase.table("distributor_vault").select("nama_distributor").execute()
            list_dist = [d['nama_distributor'] for d in res.data]
        except Exception as e:
            logging.error(f"Error fetching distributor list: {e}")
    if not list_dist: list_dist = ["Belum ada data di Database"]
    return list_dist

def get_distributor_list(supabase=None):
    """Fetch distributor list with thread-safe Streamlit caching."""
    return _fetch_distributor_list_internal()

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
