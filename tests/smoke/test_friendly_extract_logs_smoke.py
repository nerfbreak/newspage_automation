import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENGINE_SOURCE = PROJECT_ROOT / "playwright_engine.py"


class FriendlyExtractLogsSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ENGINE_SOURCE.read_text(encoding="utf-8")
        start = cls.source.index("def _dispatch_extraction_job")
        end = cls.source.index("def _navigate_to_stock_adjustment")
        cls.extract_source = cls.source[start:end]

    def test_inventory_extract_uses_user_friendly_progress_messages(self):
        expected_messages = [
            "Menyiapkan format file hasil extract",
            "Mengirim permintaan extract ke Newspage",
            "Menunggu Newspage menyiapkan file",
            "File extract berhasil diterima",
            "Membaca isi file extract",
            "File data ditemukan di dalam ZIP",
            "Extract selesai",
        ]

        for message in expected_messages:
            with self.subTest(message=message):
                self.assertIn(message, self.extract_source)

    def test_sales_extract_uses_user_friendly_completion_message(self):
        expected_messages = [
            "Menunggu Newspage menyiapkan file sales",
            "File sales berhasil diterima",
            "Extract sales selesai",
        ]

        for message in expected_messages:
            with self.subTest(message=message):
                self.assertIn(message, self.extract_source)

    def test_changed_extract_messages_do_not_use_old_jargon(self):
        old_jargon = [
            "Committing parameters to job definition",
            "Saving job and dispatching execution to server",
            "Awaiting server confirmation prompt",
            "Intercepting download link",
            "Download captured",
            "Parsing payload file",
            "ZIP target identified",
            "Payload Secured",
            "Browser closed. Ready for download.",
            "SYSTEM FAILURE",
        ]

        for phrase in old_jargon:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.extract_source)


if __name__ == "__main__":
    unittest.main()
