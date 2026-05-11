"""Process health endpoint for the Telegram bot service."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class HealthState:
    started_at: datetime = field(default_factory=_utc_now)
    last_update_at: Optional[datetime] = None

    def mark_update(self, when: Optional[datetime] = None) -> None:
        self.last_update_at = when or _utc_now()

    def payload(self, now: Optional[datetime] = None) -> dict:
        current = now or _utc_now()
        payload = {
            "status": "ok",
            "started_at": self.started_at.isoformat(),
            "last_update_at": (
                self.last_update_at.isoformat() if self.last_update_at else None
            ),
            "uptime_seconds": int((current - self.started_at).total_seconds()),
            "seconds_since_last_update": None,
        }
        if self.last_update_at is not None:
            payload["seconds_since_last_update"] = int(
                (current - self.last_update_at).total_seconds()
            )
        return payload


HEALTH_STATE = HealthState()


async def mark_update_seen(update, context) -> None:
    """PTB handler callback used to record that the bot event loop is alive."""
    HEALTH_STATE.mark_update()


class HealthcheckServer:
    def __init__(self, host: str, port: int, state: HealthState) -> None:
        self._server = _build_server(host, port, state)
        self._thread: Optional[threading.Thread] = None

    @property
    def server_address(self):
        return self._server.server_address

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="bot-healthcheck",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None


def _build_server(host: str, port: int, state: HealthState) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/healthz":
                self.send_response(404)
                self.end_headers()
                return

            body = json.dumps(state.payload()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            return

    return ThreadingHTTPServer((host, port), Handler)


def create_healthcheck_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    state: HealthState = HEALTH_STATE,
) -> HealthcheckServer:
    return HealthcheckServer(host, port, state)
