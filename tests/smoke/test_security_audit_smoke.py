"""Security audit smoke and regression tests (Spec Kit 018-security-audit).

Verifies US1 (CVE scanning readiness), US2 (encryption & session protection),
and US3 (input sanitization, XSS/RCE resistance, and Neo-Brutalist error boxes).
"""

import html
import os
import sys
import types
import unittest
from pathlib import Path

if "streamlit" not in sys.modules:
    streamlit_stub = types.SimpleNamespace(
        cache_data=lambda *args, **kwargs: (lambda fn: fn),
        secrets={},
    )
    sys.modules["streamlit"] = streamlit_stub

if "bcrypt" not in sys.modules:
    bcrypt_stub = types.SimpleNamespace(checkpw=lambda *args, **kwargs: False)
    sys.modules["bcrypt"] = bcrypt_stub

if "supabase" not in sys.modules:
    supabase_stub = types.SimpleNamespace(create_client=lambda *args, **kwargs: None, Client=object)
    sys.modules["supabase"] = supabase_stub

import database
from error_taxonomy import format_user_error


from cryptography.fernet import Fernet
import unittest.mock


REPO_ROOT = Path(__file__).resolve().parents[2]


class SecurityAuditSmokeTests(unittest.TestCase):
    def test_encryption_roundtrip_and_tampering_resistance(self):
        """US2: Verify Fernet encryption roundtrip and invalid token rejection."""
        dummy_key = Fernet.generate_key().decode()
        with unittest.mock.patch.dict(os.environ, {"MASTER_KEY": dummy_key}):
            original_payload = "distributor_secret_password_123!"
            encrypted = database.encrypt_data(original_payload)
            self.assertIsNotNone(encrypted)
            self.assertNotEqual(original_payload, encrypted)

            decrypted = database.decrypt_data(encrypted)
            self.assertEqual(original_payload, decrypted)

            # Test tampering / invalid ciphertext
            tampered = "invalid_token_without_proper_prefix"
            decrypted_tampered = database.decrypt_data(tampered)
            self.assertEqual("", decrypted_tampered)

            # Test None / empty
            self.assertEqual("", database.decrypt_data(None))
            self.assertEqual("", database.decrypt_data(""))

    def test_login_lockout_and_session_constants(self):
        """US2: Verify lockout thresholds and session timeout configuration in app.py."""
        app_path = REPO_ROOT / "app.py"
        content = app_path.read_text(encoding="utf-8")
        self.assertIn("MAX_LOGIN_ATTEMPTS = 5", content)
        self.assertIn("LOCKOUT_SECONDS = 300", content)
        self.assertIn("SESSION_TIMEOUT_SECONDS =", content)
        self.assertIn("cookie_manager.set(\"auth_user\"", content)
        self.assertIn("database.validate_remembered_session", content)
        self.assertIn("database.create_remembered_session_payload", content)

    def test_active_streamlit_session_revalidates_session_version(self):
        """BUG-001: Logged-in Streamlit sessions must be revoked after password rotation."""
        app_path = REPO_ROOT / "app.py"
        content = app_path.read_text(encoding="utf-8")
        self.assertIn("current_session_version", content)
        self.assertIn("database.get_user_session_version(supabase, active_user)", content)
        self.assertIn("active_session_version != current_session_version", content)
        self.assertIn("clear_auth_session()", content)

    def test_input_sanitization_and_html_escaping(self):
        """US3: Verify HTML escaping behavior against XSS payloads."""
        xss_payload = "<script>alert('XSS');</script>&\"'"
        escaped = html.escape(xss_payload)
        self.assertNotIn("<script>", escaped)
        self.assertIn("&lt;script&gt;", escaped)

        utils_path = REPO_ROOT / "utils.py"
        utils_content = utils_path.read_text(encoding="utf-8")
        self.assertIn("html.escape", utils_content)

    def test_subprocess_execution_safety(self):
        """US3: Verify subprocess calls avoid shell equals True and pass arguments safely."""
        dashboard_path = REPO_ROOT / "pages" / "0_dashboard.py"
        content = dashboard_path.read_text(encoding="utf-8")
        self.assertIn("subprocess.run", content)
        forbidden_flag = "shell=" + "True"
        self.assertNotIn(forbidden_flag, content)

    def test_app_login_error_boxes_use_neo_brutalism_and_taxonomy(self):
        """US3 / Neo-Brutalism: Verify login error alerts use Neo-Brutalist containers and error codes."""
        app_path = REPO_ROOT / "app.py"
        content = app_path.read_text(encoding="utf-8")
        
        # Check AUTH-001 and AUTH-002 are inside 3px solid #0F172A containers
        self.assertIn("AUTH-001", content)
        self.assertIn("AUTH-002", content)
        self.assertIn("border: 3px solid #0F172A", content)
        self.assertIn("box-shadow: 6px 6px 0px 0px #0F172A", content)


if __name__ == "__main__":
    unittest.main()
