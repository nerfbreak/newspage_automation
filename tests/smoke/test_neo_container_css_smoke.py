import os
import re
import unittest


class NeoContainerCssSmokeTests(unittest.TestCase):
    @staticmethod
    def _read_repo_file(*parts):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            *parts,
        )
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_marker_preserves_input_container_frame(self):
        content = self._read_repo_file("static", "style.css")

        self.assertIn('div[data-testid="stElementContainer"]:has(.neo-container-marker) + div', content)
        self.assertIn("border: 3px solid #0F172A !important;", content)
        self.assertIn("box-shadow: 6px 6px 0px 0px #0F172A !important;", content)

        forbidden_neutralizers = (
            'div.element-container:has(.neo-container-marker) + div:has(div[data-testid="stSelectbox"])',
            'div.element-container:has(.neo-container-marker) + div:has(div[data-testid="stTextInput"])',
            'div.element-container:has(.neo-container-marker) + div:has(div[data-testid="stDateInput"])',
            'div.element-container:has(.neo-container-marker) + div:has(div[data-testid="stNumberInput"])',
        )
        for selector in forbidden_neutralizers:
            with self.subTest(selector=selector):
                self.assertNotIn(selector, content)

    def test_stock_mutation_upload_and_mapping_groups_have_outer_containers(self):
        content = self._read_repo_file("pages", "4_stock_mutation.py")

        upload_section = content.split("# --- FILE UPLOAD + COLUMN MAPPING ---", 1)[1].split(
            "if uploaded_file is not None:", 1
        )[0]
        self.assertRegex(
            upload_section,
            re.compile(
                r"neo-container-marker.*with st\.container\(border=True\):\s+"
                r"uploaded_file = st\.file_uploader",
                re.DOTALL,
            ),
        )

        mapping_section = content.split("# --- COLUMN MAPPING ---", 1)[1].split(
            "# --- BUILD REVIEW TABLE ---", 1
        )[0]
        expected_groups = (
            ("mc1", "sku_col", "sku_metric_ph"),
            ("mc2", "desc_col", "deduct_metric_ph"),
            ("mc3", "qty_col", "add_metric_ph"),
        )
        for column, selected_value, metric_placeholder in expected_groups:
            with self.subTest(column=column):
                self.assertRegex(
                    mapping_section,
                    re.compile(
                        rf"with {column}:\s+.*neo-container-marker.*"
                        rf"with st\.container\(border=True\):.*"
                        rf"{selected_value} = st\.selectbox.*"
                        rf"{metric_placeholder} = st\.empty\(\)",
                        re.DOTALL,
                    ),
                )

        for metric_placeholder in ("sku_metric_ph", "deduct_metric_ph", "add_metric_ph"):
            self.assertIn(f"{metric_placeholder}.markdown(", content)

    def test_stock_mutation_upload_reset_uses_pre_rerun_callback(self):
        content = self._read_repo_file("pages", "4_stock_mutation.py")

        # Must not contain direct assignment to any mutasi_file_uploader key
        self.assertNotIn(
            "st.session_state.mutasi_file_uploader = None",
            content,
        )
        # Must not pop the widget key (BUG-005: pop doesn't restore dropzone)
        self.assertNotIn(
            "st.session_state.pop(\"mutasi_file_uploader\"",
            content,
        )
        # Callback must increment the uploader key counter
        self.assertRegex(
            content,
            re.compile(
                r"def _clear_mutasi_upload\(\):.*"
                r"st\.session_state\.mutasi_uploader_key \+= 1.*"
                r"st\.session_state\.mutasi_file_id = None.*"
                r"st\.session_state\.mutasi_review_df = None",
                re.DOTALL,
            ),
        )
        # Uploader must use the rotated key
        self.assertRegex(
            content,
            re.compile(
                r"st\.file_uploader\(.*"
                r"key=f[\"']mutasi_file_uploader_\{st\.session_state\.mutasi_uploader_key\}[\"']",
                re.DOTALL,
            ),
        )
        # Button must use on_click callback
        self.assertRegex(
            content,
            re.compile(
                r"st\.button\(\s*[\"']Hapus File Upload[\"'].*"
                r"on_click=_clear_mutasi_upload",
                re.DOTALL,
            ),
        )

    def test_stock_mutation_execution_tables_share_desktop_height(self):
        page_content = self._read_repo_file("pages", "4_stock_mutation.py")
        css_content = self._read_repo_file("static", "style.css")

        execution_section = page_content.split("# Dual layout", 1)[1].split(
            "# Initial table render", 1
        )[0]
        self.assertRegex(
            execution_section,
            re.compile(
                r"mutation-execution-layout-marker.*exec_col1, exec_col2 = st\.columns\(2\)",
                re.DOTALL,
            ),
        )

        self.assertIn("@media (min-width: 769px)", css_content)
        self.assertIn(":has(.mutation-execution-layout-marker)", css_content)
        self.assertRegex(
            css_content,
            re.compile(
                r":has\(\.mutation-execution-layout-marker\)[\s\S]*?\.desktop-only-table \.neo-table-wrapper[\s\S]*?height:\s*400px",
                re.DOTALL,
            ),
        )

    def test_no_unsupported_subheaders_in_execution_pages(self):
        for page_name in ["4_stock_mutation.py", "5_clearance_stock.py", "6_initial_stock.py"]:
            content = self._read_repo_file("pages", page_name)
            # Verify st.subheader is not used
            self.assertNotIn("st.subheader", content, f"Unstyled st.subheader found in {page_name}")
            # Verify section-header-underline is used instead
            self.assertIn("section-header-underline", content, f"Missing Neo-Brutalist header in {page_name}")

if __name__ == "__main__":
    unittest.main()
