"""Shared error taxonomy for safe user-facing messages and logs.

This module is intentionally side-effect free. Importing it must not initialize
Streamlit, Supabase, Playwright, or any network client.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    AUTH = "AUTH"
    SESSION = "SESSION"
    CONFIG = "CONFIG"
    DATABASE = "DATABASE"
    CREDENTIAL = "CREDENTIAL"
    INPUT = "INPUT"
    UPLOAD = "UPLOAD"
    AUTOMATION = "AUTOMATION"
    NETWORK = "NETWORK"
    NOTIFICATION = "NOTIFICATION"
    SECURITY = "SECURITY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ErrorDefinition:
    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    safe_message: str
    operator_hint: str


ERRORS: dict[str, ErrorDefinition] = {
    "AUTH-001": ErrorDefinition(
        code="AUTH-001",
        category=ErrorCategory.AUTH,
        severity=ErrorSeverity.WARNING,
        safe_message="Login failed. Check the username and password.",
        operator_hint="Authentication failed for the supplied Streamlit user.",
    ),
    "AUTH-002": ErrorDefinition(
        code="AUTH-002",
        category=ErrorCategory.AUTH,
        severity=ErrorSeverity.ERROR,
        safe_message="Account is temporarily locked after repeated failed login attempts.",
        operator_hint="Login lockout is active; verify whether attempts are legitimate.",
    ),
    "SESSION-001": ErrorDefinition(
        code="SESSION-001",
        category=ErrorCategory.SESSION,
        severity=ErrorSeverity.WARNING,
        safe_message="Session expired. Please sign in again.",
        operator_hint="Session timeout or invalid persistent cookie.",
    ),
    "CONFIG-001": ErrorDefinition(
        code="CONFIG-001",
        category=ErrorCategory.CONFIG,
        severity=ErrorSeverity.CRITICAL,
        safe_message="Application configuration is incomplete.",
        operator_hint="Check required Streamlit secrets or environment variables.",
    ),
    "DB-001": ErrorDefinition(
        code="DB-001",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        safe_message="Database request failed. Please retry or contact support.",
        operator_hint="Supabase query failed; inspect server logs for table and operation.",
    ),
    "CRED-001": ErrorDefinition(
        code="CRED-001",
        category=ErrorCategory.CREDENTIAL,
        severity=ErrorSeverity.ERROR,
        safe_message="Distributor credential is not available.",
        operator_hint="Distributor vault row is missing or incomplete.",
    ),
    "CRED-002": ErrorDefinition(
        code="CRED-002",
        category=ErrorCategory.CREDENTIAL,
        severity=ErrorSeverity.CRITICAL,
        safe_message="Distributor credential could not be decrypted.",
        operator_hint="Verify MASTER_KEY and whether the vault value is encrypted correctly.",
    ),
    "INPUT-001": ErrorDefinition(
        code="INPUT-001",
        category=ErrorCategory.INPUT,
        severity=ErrorSeverity.WARNING,
        safe_message="Input is incomplete or invalid.",
        operator_hint="User-facing validation failed before execution.",
    ),
    "UPLOAD-001": ErrorDefinition(
        code="UPLOAD-001",
        category=ErrorCategory.UPLOAD,
        severity=ErrorSeverity.WARNING,
        safe_message="Uploaded file could not be parsed.",
        operator_hint="Check file extension, workbook structure, size, and required columns.",
    ),
    "AUTO-001": ErrorDefinition(
        code="AUTO-001",
        category=ErrorCategory.AUTOMATION,
        severity=ErrorSeverity.ERROR,
        safe_message="Automation failed while opening or controlling the browser.",
        operator_hint="Playwright browser launch or install step failed.",
    ),
    "AUTO-002": ErrorDefinition(
        code="AUTO-002",
        category=ErrorCategory.AUTOMATION,
        severity=ErrorSeverity.ERROR,
        safe_message="Newspage did not respond in time.",
        operator_hint="Portal timeout, ASP.NET postback delay, or unavailable page state.",
    ),
    "AUTO-003": ErrorDefinition(
        code="AUTO-003",
        category=ErrorCategory.AUTOMATION,
        severity=ErrorSeverity.ERROR,
        safe_message="Automation could not find the expected Newspage element.",
        operator_hint="Selector or portal DOM changed; compare against element inventory.",
    ),
    "NET-001": ErrorDefinition(
        code="NET-001",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        safe_message="Network request failed.",
        operator_hint="External service, Newspage, Supabase, or Telegram request failed.",
    ),
    "NOTIFY-001": ErrorDefinition(
        code="NOTIFY-001",
        category=ErrorCategory.NOTIFICATION,
        severity=ErrorSeverity.WARNING,
        safe_message="Notification could not be sent.",
        operator_hint="Telegram or screenshot delivery failed.",
    ),
    "SEC-001": ErrorDefinition(
        code="SEC-001",
        category=ErrorCategory.SECURITY,
        severity=ErrorSeverity.CRITICAL,
        safe_message="Security guardrail blocked the operation.",
        operator_hint="Security policy, locked logic, or secret-handling rule blocked the action.",
    ),
    "UNK-001": ErrorDefinition(
        code="UNK-001",
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.ERROR,
        safe_message="Unexpected error occurred.",
        operator_hint="Unhandled exception; inspect server logs with traceback.",
    ),
}


def get_error(code: str) -> ErrorDefinition:
    """Return a known error definition, falling back to UNK-001."""
    return ERRORS.get(code, ERRORS["UNK-001"])


def format_user_error(code: str, detail: str | None = None) -> str:
    """Build a safe UI/Telegram message without exposing raw exception text."""
    definition = get_error(code)
    if detail:
        return f"[{definition.code}] {definition.safe_message} {detail}"
    return f"[{definition.code}] {definition.safe_message}"


def format_log_error(code: str, context: str | None = None) -> str:
    """Build a concise operator log prefix for detailed server-side logs."""
    definition = get_error(code)
    base = f"[{definition.code}] {definition.category.value}/{definition.severity.value}: {definition.operator_hint}"
    if context:
        return f"{base} Context: {context}"
    return base

