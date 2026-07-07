import unittest
import sys
import types
import io
import zipfile
import pandas as pd


class SessionStateDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value


# Ensure streamlit stub is present and equipped with all required methods and attributes
st_mod = sys.modules.setdefault("streamlit", types.SimpleNamespace())
if not hasattr(st_mod, "cache_data"):
    st_mod.cache_data = lambda *args, **kwargs: (lambda fn: fn)
if not hasattr(st_mod, "error"):
    st_mod.error = lambda *args, **kwargs: None
if not hasattr(st_mod, "markdown"):
    st_mod.markdown = lambda *args, **kwargs: None
if not hasattr(st_mod, "page_link"):
    st_mod.page_link = lambda *args, **kwargs: None
if not hasattr(st_mod, "toggle"):
    st_mod.toggle = lambda *args, **kwargs: None
if not hasattr(st_mod, "secrets"):
    st_mod.secrets = {}
if not hasattr(st_mod, "session_state") or not isinstance(st_mod.session_state, SessionStateDict):
    st_mod.session_state = SessionStateDict()

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
from error_taxonomy import ERRORS, ErrorCategory, ErrorSeverity, format_log_error, format_user_error
from utils import (
    render_footer,
    render_header,
    render_indicators,
    render_terminal,
    make_solid_box,
)


class NamedBytesIO(io.BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


class FakePlaceholder:
    def __init__(self):
        self.html = ""
        self.unsafe_allow_html = None

    def markdown(self, html, unsafe_allow_html=False):
        self.html = html
        self.unsafe_allow_html = unsafe_allow_html


class ExtendedOfflineSmokeTests(unittest.TestCase):
    def test_load_data_reads_excel_bytes(self):
        df_src = pd.DataFrame({"SKU": ["100500"], "Qty": ["15"]})
        buffer = io.BytesIO()
        df_src.to_excel(buffer, index=False)
        excel_file = NamedBytesIO(buffer.getvalue(), "stock_sample.xlsx")

        df_res = load_data(excel_file)
        self.assertIsNotNone(df_res)
        self.assertIn("SKU", df_res.columns)
        self.assertEqual(df_res.iloc[0]["SKU"], "100500")
        self.assertEqual(df_res.iloc[0]["Qty"], "15")

    def test_load_data_reads_generic_csv_from_zip_fallback(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as archive:
            archive.writestr("folder/random_export.csv", "SKU\tQty\n555\t99\n")
        zip_file = NamedBytesIO(zip_buffer.getvalue(), "backup.zip")

        df = load_data(zip_file)
        self.assertIsNotNone(df)
        self.assertEqual(df.columns.tolist(), ["SKU", "Qty"])
        self.assertEqual(df.iloc[0]["SKU"], "555")
        self.assertEqual(df.iloc[0]["Qty"], "99")

    def test_clean_sku_column_removes_totals_and_strips_decimals(self):
        df = pd.DataFrame({
            "SKU": ["100.0", "200.5", "Total", "Grand Total", "nan", "300 "],
            "Qty": [1, 2, 3, 4, 5, 6]
        })
        cleaned = clean_sku_column(df, "SKU", TARGET_SKUS=["100"])
        skus = cleaned["SKU"].tolist()
        self.assertIn("0100", skus)  # Target SKU prefix applied
        self.assertIn("200", skus)   # Decimal stripped
        self.assertIn("300", skus)   # Whitespace stripped
        self.assertNotIn("Total", skus)
        self.assertNotIn("Grand Total", skus)
        self.assertNotIn("nan", skus)

    def test_process_compare_filters_and_multiplies(self):
        df1 = pd.DataFrame({
            "SKU": ["100", "200"],
            "Desc": ["Item 1", "Item 2"],
            "Qty": ["10", "20"]
        })
        df2 = pd.DataFrame({
            "SKU": ["100", "200", "300"],
            "Qty": ["10", "20", "30"],
            "Aktif": ["1", "0", "1"],  # SKU 200 is inactive
            "Nama Gudang": ["GUDANG UTAMA", "GUDANG UTAMA", "GUDANG RUSAK"]  # SKU 300 is not main warehouse
        })
        multipliers = [{"sku_target": "100", "multiplier_value": 2.0}]
        merged, mismatches = process_compare(
            df1, df2,
            sku_col1="SKU", desc_col1="Desc", qty_col1="Qty",
            sku_col2="SKU", qty_col2="Qty",
            TARGET_SKUS=[], multipliers=multipliers, np_user_id="test_user"
        )
        # SKU 100 in df2: 10 * 2.0 = 20.0. df1 has 10.0. Selisih = 20.0 - 10.0 = 10.0
        sku_100_row = merged[merged["SKU"] == "100"].iloc[0]
        self.assertEqual(sku_100_row["Distributor"], 20.0)
        self.assertEqual(sku_100_row["Selisih"], 10.0)
        self.assertEqual(sku_100_row["Status"], "Mismatch")

        sku_200_row = merged[merged["SKU"] == "200"].iloc[0]
        self.assertEqual(sku_200_row["Distributor"], 0.0)  # Inactive filtered out
        self.assertEqual(sku_200_row["Status"], "Mismatch")

        self.assertNotIn("300", merged["SKU"].tolist())  # Non-main warehouse filtered out

    def test_error_taxonomy_all_definitions_valid(self):
        for code, defn in ERRORS.items():
            with self.subTest(code=code):
                self.assertEqual(defn.code, code)
                self.assertGreater(len(defn.safe_message), 0)
                self.assertGreater(len(defn.operator_hint), 0)
                self.assertIsInstance(defn.category, ErrorCategory)
                self.assertIsInstance(defn.severity, ErrorSeverity)

    def test_error_taxonomy_formatting_with_details_and_context(self):
        msg_with_detail = format_user_error("AUTH-001", "(2 attempts left)")
        self.assertTrue(msg_with_detail.endswith(" (2 attempts left)"))
        self.assertTrue(msg_with_detail.startswith("[AUTH-001]"))

        log_msg_default = format_log_error("DB-001")
        self.assertIn("[DB-001]", log_msg_default)
        self.assertIn("DATABASE/error:", log_msg_default)

        log_msg_context = format_log_error("DB-001", "custom context")
        self.assertTrue(log_msg_context.endswith("custom context"))

    def test_render_indicators_outputs_expected_user_pill(self):
        original_markdown = st_mod.markdown
        rendered = []
        try:
            st_mod.markdown = lambda html, unsafe_allow_html=False: rendered.append(html)
            st_mod.session_state["current_user"] = "Operator_1"
            render_indicators(db_status="CONNECTED", bot_status=True, bot_type="PROMO")
            html_out = rendered[0]
            self.assertIn("live-indicator", html_out)
            self.assertIn("SESSION:", html_out)
            self.assertIn("Operator_1", html_out)
        finally:
            st_mod.markdown = original_markdown

    def test_render_header_and_footer_output_neo_brutalist_markup(self):
        original_markdown = st_mod.markdown
        rendered = []
        try:
            st_mod.markdown = lambda html, unsafe_allow_html=False: rendered.append(html)
            render_header("Custom Module Title", "Sub desc")
            render_footer()
            # rendered[0] is CSS injection from render_header -> inject_css()
            header_html = rendered[1]
            footer_html = rendered[2]
            self.assertIn("Custom Module Title", header_html)
            self.assertIn("Modul otomatisasi distributor", header_html)
            self.assertIn("border: 3px solid #0F172A", header_html)
            self.assertIn("Disclaimer", footer_html)
            self.assertIn("kopi mang toni", footer_html)
        finally:
            st_mod.markdown = original_markdown

    def test_render_terminal_and_make_solid_box(self):
        placeholder = FakePlaceholder()
        render_terminal(placeholder, ["log 1", "log 2"])
        self.assertIn("log 1<br>log 2", placeholder.html)
        self.assertIn("terminal-box", placeholder.html)

        box_html = make_solid_box("Test Text", "#123456", "#654321", margin_top="12px")
        self.assertIn("background-color: #123456;", box_html)
        self.assertIn("border: 3px solid #0F172A;", box_html)
        self.assertIn("color: #654321;", box_html)
        self.assertIn("margin-top: 12px;", box_html)
        self.assertIn("Test Text", box_html)

    def test_all_ui_pages_use_error_taxonomy(self):
        import glob
        import os
        import re
        pages_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "pages")
        page_files = glob.glob(os.path.join(pages_dir, "*.py"))
        self.assertGreaterEqual(len(page_files), 6, "Must find at least 6 page files in pages/ directory")
        for filepath in page_files:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("format_user_error", content, f"{os.path.basename(filepath)} must import and use format_user_error")
            # Verify no raw st.error("string") or st.error(f"string") calls exist
            raw_errors = re.findall(r'st\.error\((?!format_user_error)[^)]+\)', content)
            self.assertEqual(len(raw_errors), 0, f"Found unstandardized st.error calls in {os.path.basename(filepath)}: {raw_errors}")


if __name__ == "__main__":
    unittest.main()

