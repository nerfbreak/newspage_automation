"""Telegram alert service - extracted from utils.py."""
import logging
import requests

from backend.config import get_settings

logger = logging.getLogger(__name__)


def send_telegram_alert(message: str):
    """Send an HTML-formatted alert via Telegram Bot API."""
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.debug("Telegram not configured, skipping alert")
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": settings.telegram_chat_id, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.warning("Telegram alert failed: %s", e)
