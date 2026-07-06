import unittest

import pandas as pd

from dashboard_log_utils import (
    build_full_activity_table_rows,
    build_recent_activity_rows,
    clean_extraction_status,
    detect_adjustment_module,
    detect_extraction_module,
    format_dashboard_timestamp,
)


class DashboardLogUtilsSmokeTests(unittest.TestCase):
    def test_module_detection_matches_dashboard_rules(self):
        self.assertEqual(detect_adjustment_module("PAC: 1 | CAR: 0"), "Mutation")
        self.assertEqual(detect_adjustment_module("5", full_name=True), "Inventory Adjustment")
        self.assertEqual(detect_extraction_module("Success (Sales)"), "Sales")
        self.assertEqual(detect_extraction_module("Success"), "Inventory")
        self.assertEqual(clean_extraction_status("Success (Sales)"), "Success")

    def test_recent_activity_rows_deduplicate_adjustment_batches(self):
        df_adj = pd.DataFrame(
            [
                {
                    "created_at": "2026-07-06T10:00:10+00:00",
                    "np_user": "NP01",
                    "run_by": "Reckitt",
                    "qty": "1",
                    "status": "Success",
                },
                {
                    "created_at": "2026-07-06T10:00:40+00:00",
                    "np_user": "NP01",
                    "run_by": "Reckitt",
                    "qty": "2",
                    "status": "Success",
                },
            ]
        )
        df_ext = pd.DataFrame(
            [
                {
                    "created_at": "2026-07-06T11:00:00+00:00",
                    "distributor_name": "Dist B",
                    "status": "Success (Sales)",
                    "extracted_by": "Nadia",
                }
            ]
        )

        rows = build_recent_activity_rows(df_adj, df_ext, {"NP01": "Dist A"})

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["mod"], "Sales")
        self.assertEqual(rows[0]["status"], "Success")
        self.assertEqual(rows[1]["dist"], "Dist A")

    def test_full_activity_table_rows_are_sorted_and_formatted(self):
        df_adj = pd.DataFrame(
            [
                {
                    "created_at": "2026-07-06T10:00:00+00:00",
                    "np_user": "NP01",
                    "run_by": "Reckitt",
                    "qty": "PAC: 1",
                    "status": "Success",
                }
            ]
        )
        df_ext = pd.DataFrame(
            [
                {
                    "created_at": "2026-07-06T12:00:00+00:00",
                    "distributor_name": "Dist B",
                    "status": "Success (Sales)",
                    "extracted_by": "Nadia",
                }
            ]
        )

        rows = build_full_activity_table_rows(df_adj, df_ext, {"NP01": "Dist A"})

        self.assertEqual(rows[0]["Distributor"], "Dist B")
        self.assertEqual(rows[0]["Module"], "Sales Extraction")
        self.assertEqual(rows[0]["Run By"], "NADIA")
        self.assertEqual(rows[1]["Module"], "Stock Mutation")
        self.assertEqual(rows[1]["Status"], "SUCCESS")

    def test_timestamp_formatter_uses_jakarta_time(self):
        self.assertEqual(
            format_dashboard_timestamp("2026-07-06T10:00:00+00:00", include_seconds=True),
            "2026-07-06 17:00:00",
        )


if __name__ == "__main__":
    unittest.main()

