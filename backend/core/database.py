"""Database module for the FastAPI backend.
Uses config.py Settings instead of st.secrets.
All Streamlit dependencies removed.
"""
import logging
import bcrypt
from cryptography.fernet import Fernet
from supabase import create_client, Client

from backend.config import get_settings

logger = logging.getLogger(__name__)

# ============================================================
# Singleton Supabase client
# ============================================================
_supabase_client: Client | None = None


def init_supabase() -> Client | None:
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    settings = get_settings()
    if settings.supabase_url and settings.supabase_key:
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        return _supabase_client
    logger.warning("Supabase URL or Key not configured")
    return None


# ============================================================
# Encryption (Fernet AES-256)
# ============================================================
def get_encryption_key() -> bytes:
    settings = get_settings()
    if not settings.master_key:
        raise ValueError("MASTER_KEY not configured")
    return settings.master_key.encode()


def encrypt_data(data: str) -> str:
    if not data:
        return ""
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    if not encrypted_data:
        return ""
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logger.error("Decryption error: %s", e)
        return ""  # Return empty string instead of ciphertext


# ============================================================
# System config
# ============================================================
_config_cache: dict = {}


def get_system_config(supabase: Client | None) -> dict:
    """Fetch system config with in-memory caching.
    Returns dict with keys: REASON_CODE, WAREHOUSE, URL_LOGIN, TIMEOUT_MS, TABLE_UPDATE_INTERVAL.
    """
    if "system_config" in _config_cache:
        return _config_cache["system_config"]

    cfg = {
        "REASON_CODE": "SA2",
        "WAREHOUSE": "GOOD_WHS",
        "URL_LOGIN": "",
        "TIMEOUT_MS": 60_000,
        "TABLE_UPDATE_INTERVAL": 5,
    }
    if supabase:
        try:
            res = supabase.table("system_config").select("*").execute()
            for row in res.data:
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
            logger.error("Error fetching system_config: %s", e)

    _config_cache["system_config"] = cfg
    return cfg


# ============================================================
# Authentication
# ============================================================
def authenticate_user(supabase: Client | None, username: str, password: str) -> bool:
    if supabase:
        try:
            res = supabase.table("users_auth").select("password").eq("username", username).execute()
            if res.data:
                hashed_pw = res.data[0]["password"].encode("utf-8")
                if bcrypt.checkpw(password.encode("utf-8"), hashed_pw):
                    return True
        except Exception as e:
            logger.error("Error authenticating user %s: %s", username, e)
    return False


# ============================================================
# Distributors
# ============================================================
_distributor_cache: dict = {}


def get_distributor_list(supabase: Client | None) -> list[str]:
    if "distributor_list" in _distributor_cache:
        return _distributor_cache["distributor_list"]

    dists: list[str] = []
    if supabase:
        try:
            res = supabase.table("distributor_vault").select("nama_distributor").execute()
            dists = [d["nama_distributor"] for d in res.data]
        except Exception as e:
            logger.error("Error fetching distributor list: %s", e)
    if not dists:
        dists = ["Belum ada data di Database"]

    _distributor_cache["distributor_list"] = dists
    return dists


def get_distributor_creds(supabase: Client | None, selected_distributor: str) -> tuple[str, str]:
    bot_user, bot_pass = "", ""
    if supabase:
        try:
            res = (
                supabase.table("distributor_vault")
                .select("np_user_id, np_password")
                .eq("nama_distributor", selected_distributor)
                .execute()
            )
            if res.data:
                bot_user = res.data[0]["np_user_id"]
                bot_pass = decrypt_data(res.data[0]["np_password"])
        except Exception as e:
            logger.error("Error fetching distributor creds for %s: %s", selected_distributor, e)
    return bot_user, bot_pass


def get_distributor_warehouse_exceptions(supabase: Client | None) -> dict[str, str]:
    exceptions: dict[str, str] = {}
    if supabase:
        try:
            res = supabase.table("distributor_exceptions").select("distributor_id, target_warehouse").execute()
            if res.data:
                for row in res.data:
                    exceptions[row["distributor_id"]] = row["target_warehouse"]
        except Exception as e:
            logger.error("Error fetching distributor_exceptions: %s", e)
    return exceptions


# ============================================================
# SKU & Multipliers
# ============================================================
_DEFAULT_SKUS = [
    "373103", "373104", "373105", "373106", "373108", "373110", "373112",
    "135428", "137118", "137120", "167209", "172130", "172131", "205901",
    "22583", "22595", "260656", "260659", "304095", "304100", "304102",
    "304157", "304161", "304164", "323044", "372264", "373100",
]


def get_target_skus(supabase: Client | None) -> list[str]:
    skus: list[str] = []
    if supabase:
        try:
            res = supabase.table("sku_formatting_rules").select("sku_code").execute()
            skus = [s["sku_code"] for s in res.data]
        except Exception as e:
            logger.error("Error fetching target skus: %s", e)
    return skus or list(_DEFAULT_SKUS)


def get_multiplier_rules(supabase: Client | None, np_user_id: str) -> list[dict]:
    rules: list[dict] = []
    if supabase and np_user_id:
        try:
            res = (
                supabase.table("distributor_sku_multiplier")
                .select("sku_target, multiplier_value")
                .eq("np_user_id", np_user_id)
                .execute()
            )
            if res.data:
                rules = res.data
        except Exception as e:
            logger.error("Error fetching multiplier rules for %s: %s", np_user_id, e)
    return rules


# ============================================================
# Logging
# ============================================================
def log_extraction_history(supabase: Client | None, distributor: str, user: str):
    if supabase:
        try:
            supabase.table("extraction_history").insert({
                "distributor_name": distributor,
                "extracted_by": user,
                "status": "Success",
            }).execute()
        except Exception as e:
            logger.error("Error logging extraction history for %s: %s", distributor, e)


def log_adjustment(supabase: Client | None, sku: str, qty, status: str, keterangan: str, bot_user: str):
    if supabase:
        try:
            safe_qty = int(qty) if str(qty).replace("-", "").isdigit() else 0
            supabase.table("adjustment_logs").insert({
                "sku": sku,
                "qty": safe_qty,
                "status": status,
                "keterangan": keterangan,
                "np_user": bot_user,
            }).execute()
        except Exception as e:
            logger.error("Error logging adjustment for SKU %s: %s", sku, e)
