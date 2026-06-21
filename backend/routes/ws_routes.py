"""WebSocket routes for real-time terminal log streaming.
Integrates with job_manager to stream Playwright job logs to the client.
Keepalive pings every 60s to prevent Render free tier spin-down.
"""
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services import job_manager
from backend.auth import decode_token

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections mapped to job IDs."""

    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[job_id] = websocket

    def disconnect(self, job_id: str):
        self.connections.pop(job_id, None)

    async def send_json(self, job_id: str, data: dict):
        ws = self.connections.get(job_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(job_id)


manager = ConnectionManager()


@router.websocket("/ws/{job_id}")
async def websocket_job_stream(websocket: WebSocket, job_id: str, token: str = ""):
    """Stream real-time logs from a running Playwright job.
    Requires a valid JWT token as query parameter: /ws/{job_id}?token=...
    """
    # Validate JWT token before accepting connection
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(job_id, websocket)
    logger.info("WebSocket connected for job: %s", job_id)

    job = job_manager.get_job(job_id)
    if not job:
        await websocket.send_json({"type": "error", "msg": f"Job {job_id} not found"})
        await websocket.close()
        return

    try:
        # Replay log history for reconnection
        history = job.get_log_history()
        if history:
            logger.info("Replaying %d historical logs for reconnected job: %s", len(history), job_id)
            for msg in history:
                await websocket.send_json(msg)

        # If job already finished, send final status and close
        if job.status in ("completed", "failed"):
            await websocket.send_json({"type": "status", "state": job.status})
            return

        # Concurrent tasks: stream logs + keepalive ping
        async def stream_logs():
            """Poll job log queue and forward to WebSocket."""
            while True:
                messages = job.drain_logs()
                for msg in messages:
                    await websocket.send_json(msg)
                    if msg.get("type") == "status" and msg.get("state") in ("completed", "failed"):
                        return
                await asyncio.sleep(0.1)

        async def keepalive():
            """Send ping every 60s to prevent Render spin-down."""
            while True:
                await asyncio.sleep(60)
                await websocket.send_json({"type": "ping"})

        # Run both tasks; cancel keepalive when stream finishes
        stream_task = asyncio.create_task(stream_logs())
        ping_task = asyncio.create_task(keepalive())

        done, pending = await asyncio.wait(
            [stream_task, ping_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for job: %s", job_id)
    except Exception as e:
        logger.error("WebSocket error for job %s: %s", job_id, e)
    finally:
        manager.disconnect(job_id)
