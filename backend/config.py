"""Centralized configuration using Pydantic BaseSettings.
Replaces all st.secrets and os.environ.get calls from the Streamlit version.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Fernet encryption key
    master_key: str = ""

    # Telegram alerts
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Newspage superuser (for promo page)
    np_user_super: str = ""
    np_pass_super: str = ""

    # JWT signing (MUST be set via JWT_SECRET env var in production)
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # Newspage constants (fetched from Supabase system_config at runtime)
    # url_login, timeout_ms, table_update_interval are stored in Supabase
    # to avoid exposing sensitive URLs in source code.

    # Auth lockout
    max_login_attempts: int = 5
    lockout_seconds: int = 300

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
