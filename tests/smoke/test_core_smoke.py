import unittest
import sys
import types

import pandas as pd

if "streamlit" not in sys.modules:
    streamlit_stub = types.SimpleNamespace(
        cache_data=lambda *args, **kwargs: (lambda fn: fn),
        error=lambda *args, **kwargs: None,
        markdown=lambda *args, **kwargs: None,
        secrets={},
        session_state={},
    )
    sys.modules["streamlit"] = streamlit_stub

if "supabase" not in sys.modules:
    supabase_stub = types.SimpleNamespace(create_client=lambda *args, **kwargs: None, Client=object)
    sys.modules["supabase"] = supabase_stub

if "requests" not in sys.modules:
    requests_stub = types.SimpleNamespace(post=lambda *args, **kwargs: None)
    sys.modules["requests"] = requests_stub

if "database" not in sys.modules:
    database_stub = types.SimpleNamespace(EXCLUDE_PREFIX=["8021803", "8021804"])
    sys.modules["database"] = database_stub

from data_processor import clean_sku_column, process_compare
from error_taxonomy import format_log_error, format_user_error, get_error
from utils import render_responsive_dataframe, safe_parse_numeric


class FakeMarkdownTarget:
    def __init__(self):
        self.html = ""
        self.unsafe_allow_html = None

    def markdown(self, html, unsafe_allow_html=False):
        self.html = html
        self.unsafe_allow_html = unsafe_allow_html


class CoreSmokeTests(unittest.TestCase):
    def test_safe_parse_numeric_handles_common_distributor_formats(self):
        cases = {
            "1,234": 1234.0,
            "1.234": 1234.0,
            "1.234,50": 1234.5,
            "1,234.50": 1234.5,
            "25-": -25.0,
            None: 0.0,
            "nan": 0.0,
            "not-a-number": 0.0,
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(safe_parse_numeric(raw), expected)

    def test_clean_sku_column_filters_empty_totals_and_formats_targets(self):
        df = pd.DataFrame({"sku": ["373103.0", " total ", None, "8021803", "abc"]})

        cleaned = clean_sku_column(df, "sku", TARGET_SKUS=["373103", "8021803"])

        self.assertEqual(cleaned["sku"].tolist(), ["0373103", "8021803", "abc"])

    def test_process_compare_returns_match_and_mismatch_rows(self):
        newspage = pd.DataFrame(
            {
                "SKU": ["100", "200"],
                "Description": ["Item A", "Item B"],
                "Qty": ["10", "5"],
            }
        )
        distributor = pd.DataFrame(
            {
                "SKU Dist": ["100", "200"],
                "Qty Dist": ["10", "8"],
                "Aktif": [1, 1],
                "Nama Gudang": ["GUDANG UTAMA", "GUDANG UTAMA"],
            }
        )

        merged, mismatches = process_compare(
            newspage,
            distributor,
            "SKU",
            "Description",
            "Qty",
            "SKU Dist",
            "Qty Dist",
            TARGET_SKUS=[],
            multipliers=[],
        )

        status_by_sku = dict(zip(merged["SKU"], merged["Status"]))
        self.assertEqual(status_by_sku["100"], "Match")
        self.assertEqual(status_by_sku["200"], "Mismatch")
        self.assertEqual(mismatches["SKU"].tolist(), ["200"])

    def test_responsive_dataframe_escapes_dynamic_values(self):
        target = FakeMarkdownTarget()
        df = pd.DataFrame({"Name": ["<script>alert(1)</script>"], "Qty": [1]})

        render_responsive_dataframe(target, df)

        self.assertTrue(target.unsafe_allow_html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", target.html)
        self.assertNotIn("<script>alert(1)</script>", target.html)
        self.assertIn("desktop-only-table", target.html)
        self.assertIn("mobile-only-cards", target.html)

    def test_error_taxonomy_formats_safe_user_and_log_messages(self):
        self.assertEqual(get_error("NOPE").code, "UNK-001")
        self.assertEqual(
            format_user_error("AUTO-002"),
            "[AUTO-002] Newspage did not respond in time.",
        )
        self.assertIn(
            "[CRED-002] CREDENTIAL/critical:",
            format_log_error("CRED-002", "vault check"),
        )


if __name__ == "__main__":
    unittest.main()
