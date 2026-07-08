import io
import ast
import re
import sys
import types
import unittest
from pathlib import Path

import pandas as pd


st_mod = sys.modules.setdefault("streamlit", types.SimpleNamespace())
if not hasattr(st_mod, "cache_data"):
    st_mod.cache_data = lambda *args, **kwargs: (lambda fn: fn)
if not hasattr(st_mod, "error"):
    st_mod.error = lambda *args, **kwargs: None
if not hasattr(st_mod, "markdown"):
    st_mod.markdown = lambda *args, **kwargs: None
if not hasattr(st_mod, "secrets"):
    st_mod.secrets = {}
if not hasattr(st_mod, "session_state"):
    st_mod.session_state = {}

if "supabase" not in sys.modules:
    sys.modules["supabase"] = types.SimpleNamespace(create_client=lambda *args, **kwargs: None, Client=object)

if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace(post=lambda *args, **kwargs: None)

if "database" not in sys.modules:
    sys.modules["database"] = types.SimpleNamespace(EXCLUDE_PREFIX=["8021803", "8021804"])

from data_processor import load_data


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_TYPES = {"csv", "xlsx", "xls"}


class NamedBytesIO(io.BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


def read_source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def uploader_type_sets(source):
    result = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_file_uploader = (
            isinstance(func, ast.Attribute)
            and func.attr == "file_uploader"
            and isinstance(func.value, ast.Name)
            and func.value.id == "st"
        )
        if not is_file_uploader:
            continue
        for keyword in node.keywords:
            if keyword.arg == "type" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                result.append(
                    {
                        item.value
                        for item in keyword.value.elts
                        if isinstance(item, ast.Constant) and isinstance(item.value, str)
                    }
                )
    return result


class UploaderFileFormatsSmokeTests(unittest.TestCase):
    def test_all_user_facing_uploaders_advertise_csv_xlsx_and_xls(self):
        page_paths = [
            "pages/1_inventory_adjustment.py",
            "pages/3_promotion_comparison.py",
            "pages/4_stock_mutation.py",
            "pages/6_initial_stock.py",
        ]

        for page_path in page_paths:
            with self.subTest(page=page_path):
                type_sets = uploader_type_sets(read_source(page_path))
                self.assertGreater(len(type_sets), 0, f"No uploader type declarations found in {page_path}")
                for accepted_types in type_sets:
                    self.assertTrue(
                        REQUIRED_TYPES.issubset(accepted_types),
                        f"{page_path} uploader accepts {sorted(accepted_types)}, expected {sorted(REQUIRED_TYPES)}",
                    )

    def test_generic_loader_reads_legacy_xls_extension(self):
        source_df = pd.DataFrame({"SKU": ["100500"], "Qty": ["15"]})
        buffer = io.BytesIO()
        source_df.to_excel(buffer, index=False)
        uploaded = NamedBytesIO(buffer.getvalue(), "legacy_stock.xls")

        parsed = load_data(uploaded)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.columns.tolist(), ["SKU", "Qty"])
        self.assertEqual(parsed.iloc[0].to_dict(), {"SKU": "100500", "Qty": "15"})

    def test_manual_and_initial_uploads_use_shared_loader(self):
        inventory_source = read_source("pages/1_inventory_adjustment.py")
        initial_source = read_source("pages/6_initial_stock.py")

        self.assertIn("df_up = data_processor.load_data(uploaded_manual)", inventory_source)
        self.assertIn("df_raw = data_processor.load_data(uploaded_file)", initial_source)


if __name__ == "__main__":
    unittest.main()
