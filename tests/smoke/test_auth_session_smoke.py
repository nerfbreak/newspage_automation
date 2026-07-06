import sys
import types
import unittest
from datetime import datetime, timezone, timedelta


if "streamlit" not in sys.modules:
    streamlit_stub = types.SimpleNamespace(
        cache_data=lambda *args, **kwargs: (lambda fn: fn),
        secrets={},
    )
    sys.modules["streamlit"] = streamlit_stub

if "bcrypt" not in sys.modules:
    bcrypt_stub = types.SimpleNamespace(checkpw=lambda *args, **kwargs: False)
    sys.modules["bcrypt"] = bcrypt_stub

if "cryptography" not in sys.modules:
    cryptography_stub = types.ModuleType("cryptography")
    fernet_stub = types.ModuleType("cryptography.fernet")

    class FakeFernet:
        def __init__(self, key):
            self.key = key

        def encrypt(self, value):
            return b"encrypted"

        def decrypt(self, value):
            return b"decrypted"

    fernet_stub.Fernet = FakeFernet
    sys.modules["cryptography"] = cryptography_stub
    sys.modules["cryptography.fernet"] = fernet_stub

if "supabase" not in sys.modules:
    supabase_stub = types.SimpleNamespace(create_client=lambda *args, **kwargs: None, Client=object)
    sys.modules["supabase"] = supabase_stub

import database


class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self, store, name):
        self.store = store
        self.name = name
        self.filters = {}
        self.pending_upsert = None
        self.pending_update = None
        self.pending_insert = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, column, value):
        self.filters[column] = value
        return self

    def upsert(self, data):
        self.pending_upsert = data
        return self

    def update(self, data):
        self.pending_update = data
        return self

    def insert(self, data):
        self.pending_insert = data
        return self

    def execute(self):
        table = self.store.setdefault(self.name, {})
        if self.pending_upsert is not None:
            username = self.pending_upsert["username"]
            table[username] = dict(self.pending_upsert)
            return FakeResult([table[username]])

        rows = list(table.values()) if isinstance(table, dict) else list(table)
        if self.pending_insert is not None:
            if isinstance(table, dict):
                key = len(table)
                table[key] = dict(self.pending_insert)
                return FakeResult([dict(table[key])])
            table.append(dict(self.pending_insert))
            return FakeResult([dict(table[-1])])
        if self.pending_update is not None:
            updated_rows = []
            for row in rows:
                if all(row.get(column) == value for column, value in self.filters.items()):
                    row.update(self.pending_update)
                    updated_rows.append(dict(row))
            return FakeResult(updated_rows)

        for column, value in self.filters.items():
            rows = [row for row in rows if row.get(column) == value]
        return FakeResult([dict(row) for row in rows])


class FakeSupabase:
    def __init__(self, store=None):
        self.store = store or {}

    def table(self, name):
        return FakeTable(self.store, name)


class AuthSessionSmokeTests(unittest.TestCase):
    def test_init_supabase_uses_environment_fallback_and_caches_client(self):
        original_client = database._supabase_client
        original_create_client = database.create_client
        original_env_url = database.os.environ.get("SUPABASE_URL")
        original_env_key = database.os.environ.get("SUPABASE_KEY")
        database._supabase_client = None
        database.os.environ["SUPABASE_URL"] = "https://env.example"
        database.os.environ["SUPABASE_KEY"] = "env-key"
        calls = []
        database.create_client = lambda url, key: calls.append((url, key)) or {"url": url, "key": key}
        try:
            first = database.init_supabase()
            second = database.init_supabase()
        finally:
            database._supabase_client = original_client
            database.create_client = original_create_client
            if original_env_url is None:
                database.os.environ.pop("SUPABASE_URL", None)
            else:
                database.os.environ["SUPABASE_URL"] = original_env_url
            if original_env_key is None:
                database.os.environ.pop("SUPABASE_KEY", None)
            else:
                database.os.environ["SUPABASE_KEY"] = original_env_key

        self.assertEqual(first, {"url": "https://env.example", "key": "env-key"})
        self.assertEqual(second, first)
        self.assertEqual(calls, [("https://env.example", "env-key")])

    def test_get_encryption_key_uses_environment_when_streamlit_secret_missing(self):
        original_master_key = database.os.environ.get("MASTER_KEY")
        database.os.environ["MASTER_KEY"] = "env-master-key"
        try:
            key = database.get_encryption_key()
        finally:
            if original_master_key is None:
                database.os.environ.pop("MASTER_KEY", None)
            else:
                database.os.environ["MASTER_KEY"] = original_master_key

        self.assertEqual(key, b"env-master-key")

    def test_encrypt_and_decrypt_return_empty_string_for_empty_input(self):
        self.assertEqual(database.encrypt_data(""), "")
        self.assertEqual(database.decrypt_data(""), "")

    def test_authenticate_user_returns_true_for_matching_password(self):
        supabase = FakeSupabase(
            {
                "users_auth": [
                    {"username": "alice", "password": "hashed-pass"},
                ]
            }
        )
        original_checkpw = database.bcrypt.checkpw
        database.bcrypt.checkpw = lambda plain, hashed: plain == b"secret" and hashed == b"hashed-pass"
        try:
            authenticated = database.authenticate_user(supabase, "alice", "secret")
        finally:
            database.bcrypt.checkpw = original_checkpw

        self.assertTrue(authenticated)

    def test_get_system_config_casts_numeric_values_and_keeps_defaults(self):
        supabase = FakeSupabase(
            {
                "system_config": [
                    {"config_key": "URL_LOGIN", "config_value": "https://example.test"},
                    {"config_key": "TIMEOUT_MS", "config_value": "90000"},
                    {"config_key": "TABLE_UPDATE_INTERVAL", "config_value": "12"},
                ]
            }
        )

        cfg = database.get_system_config(supabase)

        self.assertEqual(cfg["URL_LOGIN"], "https://example.test")
        self.assertEqual(cfg["TIMEOUT_MS"], 90000)
        self.assertEqual(cfg["TABLE_UPDATE_INTERVAL"], 12)
        self.assertEqual(cfg["REASON_CODE"], "SA2")

    def test_get_target_skus_uses_supabase_rows_when_available(self):
        supabase = FakeSupabase(
            {
                "sku_formatting_rules": [
                    {"sku_code": "111"},
                    {"sku_code": "222"},
                ]
            }
        )

        self.assertEqual(database.get_target_skus(supabase), ["111", "222"])

    def test_get_multiplier_rules_filters_by_np_user(self):
        supabase = FakeSupabase(
            {
                "distributor_sku_multiplier": [
                    {"np_user_id": "NP01", "sku_target": "SKU1", "multiplier_value": 2},
                    {"np_user_id": "NP02", "sku_target": "SKU2", "multiplier_value": 3},
                ]
            }
        )

        rules = database.get_multiplier_rules(supabase, "NP01")

        self.assertEqual(rules, [{"np_user_id": "NP01", "sku_target": "SKU1", "multiplier_value": 2}])

    def test_get_distributor_warehouse_exceptions_builds_mapping(self):
        supabase = FakeSupabase(
            {
                "distributor_exceptions": [
                    {"distributor_id": "NP01", "target_warehouse": "GOOD_WHS"},
                    {"distributor_id": "NP02", "target_warehouse": "BAD_WHS"},
                ]
            }
        )

        mapping = database.get_distributor_warehouse_exceptions(supabase)

        self.assertEqual(mapping, {"NP01": "GOOD_WHS", "NP02": "BAD_WHS"})

    def test_get_distributor_list_returns_names_and_empty_state_fallback(self):
        populated = FakeSupabase(
            {
                "distributor_vault": [
                    {"nama_distributor": "Distributor A"},
                    {"nama_distributor": "Distributor B"},
                ]
            }
        )

        self.assertEqual(
            database.get_distributor_list(populated),
            ["Distributor A", "Distributor B"],
        )
        self.assertEqual(
            database.get_distributor_list(FakeSupabase({"distributor_vault": []})),
            ["Belum ada data di Database"],
        )

    def test_get_distributor_creds_decrypts_stored_password(self):
        supabase = FakeSupabase(
            {
                "distributor_vault": [
                    {
                        "nama_distributor": "Distributor A",
                        "np_user_id": "NP01",
                        "np_password": "gAAAAencrypted",
                    }
                ]
            }
        )
        original_decrypt = database.decrypt_data
        database.decrypt_data = lambda value: "secret-pass"
        try:
            bot_user, bot_pass = database.get_distributor_creds(supabase, "Distributor A")
        finally:
            database.decrypt_data = original_decrypt

        self.assertEqual(bot_user, "NP01")
        self.assertEqual(bot_pass, "secret-pass")

    def test_get_distributor_creds_auto_encrypts_plaintext_password(self):
        store = {
            "distributor_vault": [
                {
                    "nama_distributor": "Distributor A",
                    "np_user_id": "NP01",
                    "np_password": "plain-secret",
                }
            ]
        }
        supabase = FakeSupabase(store)
        original_decrypt = database.decrypt_data
        original_encrypt = database.encrypt_data
        database.decrypt_data = lambda value: ""
        database.encrypt_data = lambda value: f"enc::{value}"
        try:
            bot_user, bot_pass = database.get_distributor_creds(supabase, "Distributor A")
        finally:
            database.decrypt_data = original_decrypt
            database.encrypt_data = original_encrypt

        self.assertEqual(bot_user, "NP01")
        self.assertEqual(bot_pass, "plain-secret")
        self.assertEqual(store["distributor_vault"][0]["np_password"], "enc::plain-secret")

    def test_get_distributor_creds_returns_blank_password_when_encrypted_value_cannot_decrypt(self):
        supabase = FakeSupabase(
            {
                "distributor_vault": [
                    {
                        "nama_distributor": "Distributor A",
                        "np_user_id": "NP01",
                        "np_password": "gAAAAdifferentkey",
                    }
                ]
            }
        )
        original_decrypt = database.decrypt_data
        database.decrypt_data = lambda value: ""
        try:
            bot_user, bot_pass = database.get_distributor_creds(supabase, "Distributor A")
        finally:
            database.decrypt_data = original_decrypt

        self.assertEqual(bot_user, "NP01")
        self.assertEqual(bot_pass, "")

    def test_log_extraction_history_inserts_expected_payload(self):
        store = {"extraction_history": []}
        supabase = FakeSupabase(store)

        database.log_extraction_history(supabase, "Distributor A", "alice", status="Sales")

        self.assertEqual(
            store["extraction_history"],
            [
                {
                    "distributor_name": "Distributor A",
                    "extracted_by": "alice",
                    "status": "Sales",
                }
            ],
        )

    def test_log_adjustment_normalizes_qty_and_keeps_run_by(self):
        store = {"adjustment_logs": []}
        supabase = FakeSupabase(store)

        database.log_adjustment(
            supabase,
            sku="SKU-1",
            qty="12.0",
            status="Success",
            keterangan="checked",
            bot_user="NP01",
            run_by="alice",
        )

        self.assertEqual(
            store["adjustment_logs"],
            [
                {
                    "sku": "SKU-1",
                    "qty": 12,
                    "status": "Success",
                    "keterangan": "checked",
                    "np_user": "NP01",
                    "run_by": "alice",
                }
            ],
        )

    def test_log_adjustment_defaults_invalid_qty_to_zero(self):
        store = {"adjustment_logs": []}
        supabase = FakeSupabase(store)

        database.log_adjustment(
            supabase,
            sku="SKU-2",
            qty="not-a-number",
            status="Failed",
            keterangan="bad input",
            bot_user="NP02",
        )

        self.assertEqual(store["adjustment_logs"][0]["qty"], 0)

    def test_reset_failed_login_clears_attempts_and_lockout(self):
        store = {
            "login_attempts": {
                "User": {
                    "username": "User",
                    "attempts": 3,
                    "lockout_until": "2026-01-01T00:00:00+00:00",
                }
            }
        }
        supabase = FakeSupabase(store)

        database.reset_failed_login(supabase, "User")

        row = store["login_attempts"]["User"]
        self.assertEqual(row["attempts"], 0)
        self.assertIsNone(row["lockout_until"])
        self.assertIn("last_attempt", row)

    def test_check_login_lockout_returns_remaining_seconds_for_active_lockout(self):
        lockout_until = datetime.now(timezone.utc) + timedelta(minutes=5)
        supabase = FakeSupabase(
            {
                "login_attempts": {
                    "User": {
                        "username": "User",
                        "attempts": 5,
                        "lockout_until": lockout_until.isoformat(),
                    }
                }
            }
        )

        is_locked, remaining, attempts = database.check_login_lockout(supabase, "User")

        self.assertTrue(is_locked)
        self.assertGreater(remaining, 0)
        self.assertEqual(attempts, 5)

    def test_expired_lockout_is_reset(self):
        expired = datetime.now(timezone.utc) - timedelta(minutes=1)
        store = {
            "login_attempts": {
                "User": {
                    "username": "User",
                    "attempts": 5,
                    "lockout_until": expired.isoformat(),
                }
            }
        }
        supabase = FakeSupabase(store)

        is_locked, remaining, attempts = database.check_login_lockout(supabase, "User")

        self.assertFalse(is_locked)
        self.assertEqual(remaining, 0)
        self.assertEqual(attempts, 0)
        self.assertEqual(store["login_attempts"]["User"]["attempts"], 0)
        self.assertIsNone(store["login_attempts"]["User"]["lockout_until"])

    def test_record_failed_login_sets_lockout_at_max_attempts(self):
        store = {
            "login_attempts": {
                "User": {
                    "username": "User",
                    "attempts": 4,
                    "lockout_until": None,
                }
            }
        }
        supabase = FakeSupabase(store)

        database.record_failed_login(supabase, "User", max_attempts=5, lockout_minutes=5)

        row = store["login_attempts"]["User"]
        self.assertEqual(row["attempts"], 5)
        self.assertIsNotNone(row["lockout_until"])
        self.assertIn("last_attempt", row)


if __name__ == "__main__":
    unittest.main()
