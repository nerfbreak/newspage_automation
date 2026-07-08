import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class LiveOperationsDocsSmokeTests(unittest.TestCase):
    def test_live_operations_runbook_contains_operational_controls(self):
        runbook = (REPO_ROOT / "docs" / "live_operations_runbook.md").read_text(encoding="utf-8")

        required_phrases = (
            "Daily Health Check",
            "Weekly Maintenance",
            "User Onboarding",
            "Access Revocation",
            "Incident Triage",
            "Rollback",
            "https://newspage.streamlit.app/healthz",
            "Dependabot",
            "python scripts/supabase_schema_check.py",
            "python scripts/supabase_rls_index_check.py",
            "python -m scripts.check_invalid_creds",
            "Do not commit `.streamlit/secrets.toml`",
        )

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, runbook)

    def test_dependabot_config_covers_runtime_and_ci_dependencies(self):
        dependabot = (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

        required_phrases = (
            'package-ecosystem: "pip"',
            'package-ecosystem: "github-actions"',
            'timezone: "Asia/Jakarta"',
            "open-pull-requests-limit: 5",
        )

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, dependabot)


if __name__ == "__main__":
    unittest.main()
