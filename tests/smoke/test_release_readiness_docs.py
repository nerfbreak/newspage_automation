import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class ReleaseReadinessDocsSmokeTests(unittest.TestCase):
    def test_release_checklist_contains_required_gates(self):
        checklist = (REPO_ROOT / "docs" / "release_readiness_checklist.md").read_text(encoding="utf-8")

        required_phrases = (
            "python scripts/production_readiness_audit.py",
            "python -m unittest discover -s tests/smoke",
            "python scripts/supabase_schema_check.py",
            "python scripts/supabase_rls_index_check.py",
            "https://newspage.streamlit.app/healthz",
            "Release Readiness",
            "Live Health Probe",
            "Session And Credential Gates",
            "Rollback Plan",
            "Manual Regression Gates",
        )

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, checklist)


if __name__ == "__main__":
    unittest.main()
