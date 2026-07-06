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

    def select(self, *args, **kwargs):
        return self

    def eq(self, column, value):
        self.filters[column] = value
        return self

    def upsert(self, data):
        self.pending_upsert = data
        return self

    def execute(self):
        table = self.store.setdefault(self.name, {})
        if self.pending_upsert is not None:
            username = self.pending_upsert["username"]
            table[username] = dict(self.pending_upsert)
            return FakeResult([table[username]])

        rows = list(table.values()) if isinstance(table, dict) else list(table)
        for column, value in self.filters.items():
            rows = [row for row in rows if row.get(column) == value]
        return FakeResult([dict(row) for row in rows])


class FakeSupabase:
    def __init__(self, store=None):
        self.store = store or {}

    def table(self, name):
        return FakeTable(self.store, name)


class AuthSessionSmokeTests(unittest.TestCase):
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
