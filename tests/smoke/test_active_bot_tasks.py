"""Offline smoke tests for active bot task tracking (Spec-035)."""
import unittest


class _MockResponse:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return self


class _MockTable:
    def __init__(self, rows=None):
        self._rows = rows or []

    def insert(self, payload):
        return _MockResponse([{"id": "test-uuid-123", **payload}])

    def delete(self):
        return self

    def select(self, cols):
        return self

    def eq(self, key, val):
        return _MockResponse(self._rows)

    def order(self, col, desc=False):
        return _MockResponse(self._rows)


class _MockSupabase:
    def __init__(self, rows=None):
        self._rows = rows or []

    def table(self, name):
        return _MockTable(self._rows)


class ActiveBotTasksSmokeTests(unittest.TestCase):

    def test_register_returns_id(self):
        from database import register_active_task
        task_id = register_active_task(_MockSupabase(), "Test Task", "Dist A", "user1")
        self.assertEqual(task_id, "test-uuid-123")

    def test_register_returns_none_without_supabase(self):
        from database import register_active_task
        self.assertIsNone(register_active_task(None, "T", "D", "U"))

    def test_clear_does_not_raise(self):
        from database import clear_active_task
        clear_active_task(_MockSupabase(), "some-id")  # should not raise

    def test_clear_skips_none_id(self):
        from database import clear_active_task
        clear_active_task(_MockSupabase(), None)  # should not raise

    def test_clear_for_user_does_not_raise(self):
        from database import clear_active_tasks_for_user
        clear_active_tasks_for_user(_MockSupabase(), "user1")

    def test_get_active_tasks_returns_list(self):
        from database import get_active_tasks
        rows = [{"id": "1", "task_type": "X", "distributor_name": "D", "started_by": "U"}]
        result = get_active_tasks(_MockSupabase(rows))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["task_type"], "X")

    def test_get_active_tasks_empty(self):
        from database import get_active_tasks
        self.assertEqual(get_active_tasks(_MockSupabase()), [])

    def test_get_active_tasks_none_supabase(self):
        from database import get_active_tasks
        self.assertEqual(get_active_tasks(None), [])

    def test_schema_check_includes_active_bot_tasks(self):
        from scripts.supabase_schema_check import REQUIRED_SCHEMA
        self.assertIn("active_bot_tasks", REQUIRED_SCHEMA)
        cols = REQUIRED_SCHEMA["active_bot_tasks"]
        self.assertIn("task_type", cols)
        self.assertIn("distributor_name", cols)
        self.assertIn("started_by", cols)
        self.assertIn("started_at", cols)


if __name__ == "__main__":
    unittest.main()
