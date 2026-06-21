"""Authentication module: JWT tokens, bcrypt verification, lockout logic.
Mirrors the brute-force protection from app.py.
"""
import html
import time
import logging
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from backend.config import get_settings
from backend.core.database import init_supabase, authenticate_user

logger = logging.getLogger(__name__)

# ============================================================
# In-memory lockout tracking (mirrors app.py)
# ============================================================
_failed_attempts: dict[str, dict] = {}
# key: username, value: {"count": int, "lockout_until": float}


def _check_lockout(username: str) -> tuple[bool, int]:
    """Return (is_locked, remaining_seconds)."""
    info = _failed_attempts.get(username)
    if not info:
        return False, 0
    if info["lockout_until"] > 0:
        remaining = int(info["lockout_until"] - time.time())
        if remaining > 0:
            return True, remaining
        # Lockout expired, reset
        _failed_attempts.pop(username, None)
        return False, 0
    return False, 0


def _record_failure(username: str):
    settings = get_settings()
    info = _failed_attempts.setdefault(username, {"count": 0, "lockout_until": 0})
    info["count"] += 1
    if info["count"] >= settings.max_login_attempts:
        info["lockout_until"] = time.time() + settings.lockout_seconds
        # Send Telegram alert
        from backend.services.telegram_service import send_telegram_alert
        send_telegram_alert(
            f"[ALERT] Account lockout triggered for user: <b>{html.escape(username)}</b>\n"
            f"{info['count']} failed attempts."
        )


def _clear_failures(username: str):
    _failed_attempts.pop(username, None)


# ============================================================
# JWT Token helpers
# ============================================================
def create_access_token(username: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": username, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(username: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {"sub": username, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload dict or None on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.debug("JWT decode failed: %s", e)
        return None


# ============================================================
# High-level login flow
# ============================================================
def perform_login(username: str, password: str) -> dict:
    """
    Attempt login. Returns:
      {"ok": True, "access_token": ..., "refresh_token": ..., "expires_in": ...}
    or
      {"ok": False, "error": ..., "locked": bool, "remaining": int, "attempts_left": int}
    """
    settings = get_settings()

    # Check lockout
    is_locked, remaining = _check_lockout(username)
    if is_locked:
        return {"ok": False, "error": "Account locked", "locked": True, "remaining": remaining}

    # Authenticate against Supabase
    supabase = init_supabase()
    if authenticate_user(supabase, username, password):
        _clear_failures(username)
        access = create_access_token(username)
        refresh = create_refresh_token(username)
        return {
            "ok": True,
            "access_token": access,
            "refresh_token": refresh,
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
        }

    # Failed attempt
    _record_failure(username)
    info = _failed_attempts.get(username, {})
    attempts_left = max(0, settings.max_login_attempts - info.get("count", 0))
    locked = info.get("lockout_until", 0) > time.time()

    return {
        "ok": False,
        "error": "Invalid credentials",
        "locked": locked,
        "remaining": int(info.get("lockout_until", 0) - time.time()) if locked else 0,
        "attempts_left": attempts_left,
    }


def perform_refresh(refresh_token: str) -> dict:
    """Validate refresh token and issue new access token."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return {"ok": False, "error": "Invalid refresh token"}

    username = payload.get("sub")
    if not username:
        return {"ok": False, "error": "Invalid token payload"}

    settings = get_settings()
    access = create_access_token(username)
    return {
        "ok": True,
        "access_token": access,
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
    }
