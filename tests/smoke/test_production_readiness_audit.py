import unittest

from scripts.production_readiness_audit import render_markdown, run_audit


class ProductionReadinessAuditSmokeTests(unittest.TestCase):
    def test_static_production_readiness_audit_has_no_failures(self):
        findings = run_audit()
        failures = [finding for finding in findings if finding.status == "FAIL"]

        self.assertEqual(failures, [])

    def test_markdown_renderer_includes_summary_and_table(self):
        rendered = render_markdown(run_audit())

        self.assertIn("# Production Readiness Audit", rendered)
        self.assertIn("| Check | Status | Detail |", rendered)
        self.assertIn("required-artifact", rendered)
        self.assertIn("root-debug-artifacts", rendered)


if __name__ == "__main__":
    unittest.main()
