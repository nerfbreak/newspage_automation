import unittest
import sys
import types
import io
import zipfile

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

from data_processor import clean_sku_column, load_data, process_compare
from error_taxonomy import format_log_error, format_user_error, get_error
from utils import (
    clean_html,
    decode_param,
    encode_param,
    make_error_box,
    make_solid_box,
    make_success_box,
    make_terminal_logger,
    render_neo_table,
    render_metric_card,
    render_responsive_dataframe,
    resolve_distributor_url,
    safe_parse_numeric,
)


class FakeMarkdownTarget:
    def __init__(self):
        self.html = ""
        self.unsafe_allow_html = None

    def markdown(self, html, unsafe_allow_html=False):
        self.html = html
        self.unsafe_allow_html = unsafe_allow_html


class NamedBytesIO(io.BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


class FakeQueryParams(dict):
    pass


class CoreSmokeTests(unittest.TestCase):
    def test_param_encoding_round_trip_and_invalid_decode_fallback(self):
        raw = "Distributor A / 2026-07-06"
        encoded = encode_param(raw)

        self.assertNotEqual(encoded, raw)
        self.assertEqual(decode_param(encoded), raw)
        self.assertEqual(decode_param("%%%not-base64%%%"), "%%%not-base64%%%")

    def test_load_data_reads_comma_csv_after_tab_fallback(self):
        csv_file = NamedBytesIO(b"SKU,Qty\n100,5\n200,7\n", "stock.csv")

        df = load_data(csv_file)

        self.assertEqual(df.columns.tolist(), ["SKU", "Qty"])
        self.assertEqual(df["SKU"].tolist(), ["100", "200"])
        self.assertEqual(df["Qty"].tolist(), ["5", "7"])

    def test_load_data_reads_invt_master_csv_from_zip(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as archive:
            archive.writestr("folder/INVT_MASTER_EXPORT.csv", "SKU\tQty\n100\t5\n")
            archive.writestr("folder/other.csv", "Other\tValue\nx\t1\n")
        zip_file = NamedBytesIO(zip_buffer.getvalue(), "export.zip")

        df = load_data(zip_file)

        self.assertEqual(df.columns.tolist(), ["SKU", "Qty"])
        self.assertEqual(df.iloc[0].to_dict(), {"SKU": "100", "Qty": "5"})

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

    def test_process_compare_filters_inactive_and_non_main_warehouse_rows(self):
        newspage = pd.DataFrame(
            {
                "SKU": ["100"],
                "Description": ["Item A"],
                "Qty": ["10"],
            }
        )
        distributor = pd.DataFrame(
            {
                "SKU Dist": ["100", "100", "100"],
                "Qty Dist": ["10", "99", "88"],
                "Aktif": [1, 0, 1],
                "Nama Gudang": ["GUDANG UTAMA", "GUDANG UTAMA", "GUDANG RETUR"],
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

        self.assertEqual(merged.loc[merged["SKU"] == "100", "Distributor"].iloc[0], 10)
        self.assertTrue(mismatches.empty)

    def test_process_compare_applies_multiplier_rules_before_matching(self):
        newspage = pd.DataFrame(
            {
                "SKU": ["SKU-1"],
                "Description": ["Item A"],
                "Qty": ["20"],
            }
        )
        distributor = pd.DataFrame(
            {
                "SKU Dist": ["SKU-1"],
                "Qty Dist": ["10"],
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
            multipliers=[{"sku_target": "SKU-1", "multiplier_value": 2}],
        )

        self.assertEqual(merged.loc[merged["SKU"] == "SKU-1", "Distributor"].iloc[0], 20)
        self.assertTrue(mismatches.empty)

    def test_responsive_dataframe_escapes_dynamic_values(self):
        target = FakeMarkdownTarget()
        df = pd.DataFrame({"Name": ["<script>alert(1)</script>"], "Qty": [1]})

        render_responsive_dataframe(target, df)

        self.assertTrue(target.unsafe_allow_html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", target.html)
        self.assertNotIn("<script>alert(1)</script>", target.html)
        self.assertIn("desktop-only-table", target.html)
        self.assertIn("mobile-only-cards", target.html)

    def test_terminal_logger_escapes_messages(self):
        target = FakeMarkdownTarget()
        ui_log, history = make_terminal_logger(target)

        ui_log("BOT", "<b>danger</b>")

        self.assertEqual(len(history), 1)
        self.assertIn("&lt;b&gt;danger&lt;/b&gt;", history[0])
        self.assertNotIn("<b>danger</b>", history[0])
        self.assertIn("terminal-box", target.html)
        self.assertTrue(target.unsafe_allow_html)

    def test_clean_html_compacts_multiline_markup(self):
        raw = "\n  <div>\n    Hello\n  </div>\n"

        self.assertEqual(clean_html(raw), " <div> Hello </div>")

    def test_render_metric_card_escapes_title_and_value(self):
        html = render_metric_card("<admin>", "<script>alert(1)</script>", accent=True)

        self.assertIn("&lt;admin&gt;", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_alert_boxes_escape_dynamic_text(self):
        for factory in (make_solid_box, make_success_box, make_error_box):
            with self.subTest(factory=factory.__name__):
                if factory is make_solid_box:
                    rendered = factory("<script>alert(1)</script>", "#0068C9", "#0068C9")
                else:
                    rendered = factory("<script>alert(1)</script>")

                self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", rendered)
                self.assertNotIn("<script>alert(1)</script>", rendered)

    def test_render_neo_table_escapes_values_and_formats_integral_float(self):
        target = FakeMarkdownTarget()
        df = pd.DataFrame({"Name": ["<b>bad</b>"], "Qty": [2.0]})

        render_neo_table(target, df)

        self.assertTrue(target.unsafe_allow_html)
        self.assertIn("&lt;b&gt;bad&lt;/b&gt;", target.html)
        self.assertNotIn("<b>bad</b>", target.html)
        self.assertIn("<td>2</td>", target.html)

    def test_resolve_distributor_url_handles_encoded_and_plain_params(self):
        original_query_params = sys.modules["streamlit"].query_params if hasattr(sys.modules["streamlit"], "query_params") else None
        encoded_params = FakeQueryParams({"d": encode_param("Distributor B")})
        plain_params = FakeQueryParams({"distributor": "Distributor A"})
        try:
            sys.modules["streamlit"].query_params = encoded_params
            self.assertEqual(resolve_distributor_url(["Distributor A", "Distributor B"]), ("Distributor B", 1))

            sys.modules["streamlit"].query_params = plain_params
            self.assertEqual(resolve_distributor_url(["Distributor A", "Distributor B"]), ("Distributor A", 0))
            self.assertNotIn("distributor", plain_params)
        finally:
            if original_query_params is None:
                delattr(sys.modules["streamlit"], "query_params")
            else:
                sys.modules["streamlit"].query_params = original_query_params

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
