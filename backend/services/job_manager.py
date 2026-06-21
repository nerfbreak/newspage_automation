"""Job manager: thread-safe job queue with single concurrent Playwright lock.
Manages background Playwright operations and streams logs via queue.Queue.
"""
import uuid
import time
import threading
import queue
import logging
from datetime import datetime, timezone, timedelta
from typing import Callable, Any

logger = logging.getLogger(__name__)

# ============================================================
# Global state
# ============================================================
_playwright_lock = threading.Lock()  # Single concurrent Playwright job
_jobs: dict[str, dict] = {}  # Active job registry


class Job:
    """Represents a background Playwright job."""

    def __init__(self, job_id: str, job_type: str):
        self.job_id = job_id
        self.job_type = job_type
        self.status = "queued"  # queued, running, completed, failed
        self.log_queue: queue.Queue = queue.Queue()
        self.log_history: list[dict] = []  # All logs for replay on reconnection
        self.result: dict | None = None
        self.progress_current = 0
        self.progress_total = 0
        self.created_at = time.time()
        self._thread: threading.Thread | None = None
        # File storage (for download endpoints)
        self.file_data: bytes | None = None
        self.file_name: str = ""

    def start(self, target: Callable, args: tuple):
        """Start the job in a background thread."""
        self.status = "running"
        self._thread = threading.Thread(target=self._run, args=(target, args), daemon=True)
        self._thread.start()

    def _run(self, target: Callable, args: tuple):
        try:
            target(*args)
            if self.status == "running":
                self.status = "completed"
        except Exception as e:
            logger.error("Job %s failed: %s", self.job_id, e)
            self.status = "failed"
            self._push_log("ERROR", f"Job failed: {e}")
            self._push_status("failed")

    def _push_log(self, module: str, msg: str):
        """Push a log message to the queue (thread-safe)."""
        now = datetime.now(timezone(timedelta(hours=7)))
        self.log_queue.put({
            "type": "log",
            "module": module,
            "msg": msg,
            "timestamp": now.strftime("%H:%M:%S"),
            "elapsed_ms": int((time.time() - self.created_at) * 1000),
        })

    def _push_progress(self, current: int, total: int):
        self.progress_current = current
        self.progress_total = total
        self.log_queue.put({"type": "progress", "current": current, "total": total})

    def _push_status(self, state: str):
        self.status = state
        self.log_queue.put({"type": "status", "state": state})

    def _push_file_ready(self, download_url: str, filename: str):
        self.log_queue.put({
            "type": "file_ready",
            "download_url": download_url,
            "filename": filename,
        })

    # ---- Callbacks for playwright_adapter ----
    def ui_log(self, module: str, msg: str):
        """Callback for playwright_adapter ui_log parameter."""
        self._push_log(module, msg)

    def alert_callback(self, message: str):
        """Callback for telegram alerts."""
        from backend.services.telegram_service import send_telegram_alert
        send_telegram_alert(message)

    def progress_callback(self, current: int, total: int):
        """Callback for progress updates."""
        self._push_progress(current, total)

    def result_callback(self, result: dict):
        """Callback for final results."""
        self.result = result
        if result.get("type") == "file":
            self.file_data = result.get("data")
            self.file_name = result.get("filename", "")
            self._push_file_ready(
                f"/api/download/{self.job_id}",
                self.file_name,
            )
            self._push_status("completed")
        elif result.get("type") == "dataframe":
            self._push_status("completed")
        elif result.get("type") == "execution_done":
            self._push_status("completed")
        elif result.get("type") == "error":
            self._push_status("failed")

    def drain_logs(self) -> list[dict]:
        """Non-blocking drain of all pending log messages. Also stores in history for replay."""
        messages = []
        while True:
            try:
                msg = self.log_queue.get_nowait()
                messages.append(msg)
                self.log_history.append(msg)
            except queue.Empty:
                break
        return messages

    def get_log_history(self) -> list[dict]:
        """Return all historical logs for reconnection replay."""
        return list(self.log_history)


# ============================================================
# Public API
# ============================================================

def submit_job(job_type: str, target: Callable, args: tuple) -> dict:
    """Submit a new Playwright job. Returns {"job_id": ..., "status": ...}.
    Raises RuntimeError if another Playwright job is already running.
    """
    # Check lock (non-blocking)
    if not _playwright_lock.acquire(blocking=False):
        raise RuntimeError("Another Playwright job is already running. Please wait.")

    job_id = str(uuid.uuid4())[:8]
    job = Job(job_id, job_type)
    _jobs[job_id] = job

    def _wrapped_target(*a):
        try:
            target(*a)
        finally:
            _playwright_lock.release()

    job.start(_wrapped_target, args)
    logger.info("Job %s (%s) started", job_id, job_type)
    return {"job_id": job_id, "status": "running"}


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def get_job_status(job_id: str) -> dict | None:
    job = _jobs.get(job_id)
    if not job:
        return None
    return {
        "job_id": job_id,
        "status": job.status,
        "progress": job.progress_current,
        "total": job.progress_total,
    }


def cleanup_old_jobs(max_age_seconds: int = 3600):
    """Remove completed/failed jobs older than max_age_seconds."""
    now = time.time()
    to_remove = [
        jid for jid, j in _jobs.items()
        if j.status in ("completed", "failed") and (now - j.created_at) > max_age_seconds
    ]
    for jid in to_remove:
        _jobs.pop(jid, None)
