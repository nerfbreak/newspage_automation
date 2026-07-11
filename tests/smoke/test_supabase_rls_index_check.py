import unittest

from scripts.supabase_rls_index_check import REQUIRED_TABLES, SETUP_SQL, _parse_rpc_response


class SupabaseRLSIndexCheckSmokeTests(unittest.TestCase):
    def test_required_tables_contains_all_critical_tables(self):
        self.assertEqual(len(REQUIRED_TABLES), 11)
        self.assertIn("users_auth", REQUIRED_TABLES)
        self.assertIn("distributor_vault", REQUIRED_TABLES)
        self.assertIn("adjustment_logs", REQUIRED_TABLES)
        self.assertIn("extraction_history", REQUIRED_TABLES)
        self.assertIn("uploaded_files", REQUIRED_TABLES)
        self.assertIn("active_bot_tasks", REQUIRED_TABLES)

    def test_setup_sql_contains_required_tables_and_grants(self):
        self.assertIn("create or replace function verify_rls_and_indexes()", SETUP_SQL)
        self.assertIn("grant execute on function verify_rls_and_indexes() to anon, authenticated;", SETUP_SQL)
        for table in REQUIRED_TABLES:
            self.assertIn(f"'{table}'", SETUP_SQL)

    def test_parse_rpc_response_with_rls_enabled_and_indexes(self):
        payload = {
            "rls_status": [{"table": t, "rls_enabled": True} for t in REQUIRED_TABLES],
            "indexes": [{"table": t, "index_name": f"{t}_pkey", "index_def": "CREATE UNIQUE INDEX"} for t in REQUIRED_TABLES],
        }
        checks = _parse_rpc_response(payload)
        self.assertEqual(len(checks), 22)
        for check in checks:
            self.assertEqual(check.status, "PASS", f"Failed for {check.table} ({check.check_type}): {check.detail}")

    def test_parse_rpc_response_with_missing_rls(self):
        payload = {
            "rls_status": [
                {"table": t, "rls_enabled": False if t == "uploaded_files" else True} for t in REQUIRED_TABLES
            ],
            "indexes": [{"table": t, "index_name": f"{t}_pkey"} for t in REQUIRED_TABLES],
        }
        checks = _parse_rpc_response(payload)
        uploaded_rls = [c for c in checks if c.table == "uploaded_files" and c.check_type == "RLS"][0]
        self.assertEqual(uploaded_rls.status, "FAIL")
        self.assertIn("NOT enabled", uploaded_rls.detail)

    def test_parse_rpc_response_with_missing_index(self):
        payload = {
            "rls_status": [{"table": t, "rls_enabled": True} for t in REQUIRED_TABLES],
            "indexes": [{"table": t, "index_name": f"{t}_pkey"} for t in REQUIRED_TABLES if t != "system_config"],
        }
        checks = _parse_rpc_response(payload)
        sys_idx = [c for c in checks if c.table == "system_config" and c.check_type == "INDEX"][0]
        self.assertEqual(sys_idx.status, "WARN")
        self.assertIn("No indexes found", sys_idx.detail)


if __name__ == "__main__":
    unittest.main()
