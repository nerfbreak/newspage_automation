import sys
import types
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import pandas as pd


class FakeProgress:
    def __init__(self, initial):
        self.values = [initial]

    def progress(self, value):
        self.values.append(value)


class FakeEmpty:
    def markdown(self, *args, **kwargs):
        return None

    def empty(self):
        return None


class FakeSessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value


created_progress = []


def fake_progress(initial):
    progress = FakeProgress(initial)
    created_progress.append(progress)
    return progress


st_mod = sys.modules.setdefault("streamlit", types.SimpleNamespace())
st_mod.progress = fake_progress
st_mod.empty = lambda: FakeEmpty()
st_mod.markdown = lambda *args, **kwargs: None
st_mod.toast = lambda *args, **kwargs: None
st_mod.error = lambda *args, **kwargs: None
st_mod.session_state = FakeSessionState(dry_run_enabled=False)

if "database" not in sys.modules:
    sys.modules["database"] = types.SimpleNamespace(
        get_distributor_warehouse_exceptions=lambda supabase: {},
        log_adjustment=lambda *args, **kwargs: None,
    )

if "utils" not in sys.modules:
    sys.modules["utils"] = types.SimpleNamespace(
        render_responsive_dataframe=lambda *args, **kwargs: None,
        make_success_box=lambda message: message,
        make_error_box=lambda message: message,
    )

if "playwright" not in sys.modules:
    playwright_mod = types.ModuleType("playwright")
    sync_api_mod = types.ModuleType("playwright.sync_api")
    sync_api_mod.TimeoutError = TimeoutError
    sync_api_mod.sync_playwright = lambda: None
    sys.modules["playwright"] = playwright_mod
    sys.modules["playwright.sync_api"] = sync_api_mod

import playwright_engine


class FakeLocator:
    def click(self, *args, **kwargs):
        return None

    def wait_for(self, *args, **kwargs):
        return None


class FakePage:
    def locator(self, *args, **kwargs):
        return FakeLocator()

    def once(self, *args, **kwargs):
        return None

    def wait_for_timeout(self, *args, **kwargs):
        return None


class FakeBrowser:
    def close(self):
        return None


@contextmanager
def fake_browser_session(*args, **kwargs):
    yield FakePage(), FakeBrowser()


class ManualProgressSmokeTests(unittest.TestCase):
    def setUp(self):
        created_progress.clear()
        st_mod.session_state.clear()
        st_mod.session_state["dry_run_enabled"] = False

    def test_manual_execution_default_progress_reaches_full_on_success(self):
        df_view = pd.DataFrame(
            [
                {"SKU": "1001", "PAC": 1, "CAR": 0, "EA": 0},
                {"SKU": "1002", "PAC": 0, "CAR": 1, "EA": 0},
                {"SKU": "1003", "PAC": 0, "CAR": 0, "EA": 1},
            ]
        )

        with patch.object(playwright_engine, "ensure_playwright", lambda: None), \
            patch.object(playwright_engine, "managed_browser_session", fake_browser_session), \
            patch.object(playwright_engine, "_setup_terminate_button", lambda *args, **kwargs: None), \
            patch.object(playwright_engine, "_setup_progress_layout", lambda *args, **kwargs: object()), \
            patch.object(playwright_engine, "_update_progress_text", lambda *args, **kwargs: None), \
            patch.object(playwright_engine, "_navigate_to_stock_adjustment", lambda *args, **kwargs: None), \
            patch.object(playwright_engine, "_inject_manual_adjustment_row", lambda *args, **kwargs: None), \
            patch.object(playwright_engine, "_wait_for_page_ready", lambda *args, **kwargs: None), \
            patch.object(playwright_engine, "_capture_stkadj_success_screenshot", lambda *args, **kwargs: "success.png"), \
            patch.object(playwright_engine, "_log_df_to_supabase", lambda *args, **kwargs: None), \
            patch.object(playwright_engine.database, "get_distributor_warehouse_exceptions", lambda supabase: {}), \
            patch.object(playwright_engine.utils, "render_responsive_dataframe", lambda *args, **kwargs: None), \
            patch.object(playwright_engine.utils, "make_success_box", lambda message: message):
            result = playwright_engine.run_execution_manual(
                df_view,
                "bot_user",
                "bot_pass",
                "Distributor",
                "https://example.invalid",
                1000,
                "GOOD_WHS",
                "REASON",
                1,
                lambda *args, **kwargs: None,
                lambda *args, **kwargs: None,
                FakeEmpty(),
                FakeEmpty(),
                None,
                remark_text="manual progress smoke",
                current_user="tester",
            )

        self.assertEqual(result[:2], (3, 0))
        self.assertEqual(created_progress[-1].values[-1], 1.0)


if __name__ == "__main__":
    unittest.main()
