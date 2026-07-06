import unittest

from scripts.supabase_schema_check import REQUIRED_SCHEMA, _summarize_supabase_error


class SupabaseSchemaCheckSmokeTests(unittest.TestCase):
    def test_required_schema_tracks_critical_added_columns(self):
        self.assertIn("run_by", REQUIRED_SCHEMA["adjustment_logs"])
        self.assertIn("status", REQUIRED_SCHEMA["extraction_history"])
        self.assertIn("file_content_base64", REQUIRED_SCHEMA["uploaded_files"])

    def test_supabase_error_summary_is_safe_and_actionable(self):
        summary = _summarize_supabase_error(
            400,
            '{"code":"42703","message":"column uploaded_files.file_content_base64 does not exist","hint":"Check schema"}',
        )

        self.assertIn("HTTP 400 42703", summary)
        self.assertIn("file_content_base64", summary)
        self.assertNotIn("SUPABASE_KEY", summary)


if __name__ == "__main__":
    unittest.main()
