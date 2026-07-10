import pytest
from database import register_active_task, clear_active_task, get_active_tasks

class MockResponse:
    def __init__(self, data):
        self.data = data
    def execute(self):
        return self

class MockQuery:
    def __init__(self, table, op, return_data):
        self.table = table
        self.op = op
        self.return_data = return_data
    def insert(self, payload):
        return MockResponse([{"id": "12345"}])
    def delete(self):
        return self
    def eq(self, key, val):
        return MockResponse(self.return_data)
    def select(self, cols):
        return self
    def order(self, col, desc=False):
        return MockResponse(self.return_data)

class MockSupabase:
    def __init__(self):
        self.tasks = []
    def table(self, name):
        if name == "active_bot_tasks":
            return MockQuery(name, "all", self.tasks)
        return MockQuery(name, "all", [])

def test_register_active_task():
    db = MockSupabase()
    task_id = register_active_task(db, "Test Task", "Dist A", "User A")
    assert task_id == "12345"

def test_get_active_tasks():
    db = MockSupabase()
    db.tasks = [{"id": "1", "task_type": "Test", "distributor_name": "A", "started_by": "User"}]
    tasks = get_active_tasks(db)
    assert len(tasks) == 1
    assert tasks[0]["task_type"] == "Test"
