import os
import unittest


class NeoContainerCssSmokeTests(unittest.TestCase):
    def test_marker_preserves_input_container_frame(self):
        css_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "static",
            "style.css",
        )
        with open(css_path, "r", encoding="utf-8") as f:
            content = f.read()

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


if __name__ == "__main__":
    unittest.main()
