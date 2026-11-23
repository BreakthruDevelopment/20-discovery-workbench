"""`GET /healthz` and `GET /`, and `wb serve` which binds them.

`/healthz` reports the package version and one replay round-trip through app 17's
loop. The reply is recorded in this module. There is no Bedrock call and no
source read: a deploy can smoke this without a database or the discovery pack.

`GET /` serves the committed exam-coverage map. It does not regenerate it. The
line numbers stay what `scripts/coverage_map.py` wrote, and pytest is what fails
when they drift.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from agent_container.core.budget import Budget
from agent_container.core.loop import AgentLoop, EndReason
from agent_container.core.provider import ModelProvider
from agent_container.core.replay import ReplayProvider

from workbench import __version__
from workbench.cli.coverage import map_path

_RECORDED_TEXT = "replay-ok"
_TEXT = "text/plain; charset=utf-8"


class Server(ThreadingHTTPServer):
    """The two-route server. Threads are daemons so a test can shut it down."""

    allow_reuse_address = True
    daemon_threads = True


def replay_round_trip(provider: ModelProvider | None = None) -> tuple[bool, str]:
    """One recorded converse through the agent loop. `(ok, stop_reason)`.

    `ok` means the loop ended because the recorded reply's stop reason was
    `end_turn`, and the text that came back is the text that was recorded. A
    provider that does anything else is a failed round-trip, not a quiet success.
    """
    chosen = _recorded_provider() if provider is None else provider
    agent = AgentLoop(chosen, system_prompt="Health check. Recorded replies only.")
    try:
        result = asyncio.run(
            agent.run("ping", Budget(max_turns=2, max_tokens=1_000, max_seconds=5.0))
        )
    except Exception:
        return False, "none"
    stop = _token(result.stop_reason or "none")
    ok = (
        result.end_reason is EndReason.END_TURN
        and result.stop_reason == "end_turn"
        and result.final_text == _RECORDED_TEXT
    )
    return ok, stop


def health_body() -> tuple[int, str]:
    """`(status, body)` for `GET /healthz`."""
    ok, stop_reason = replay_round_trip()
    lines = [
        f"version: {__version__}",
        f"replay: {'ok' if ok else 'failed'}",
        f"stop_reason: {stop_reason}",
    ]
    return (200 if ok else 500), "\n".join(lines) + "\n"


def coverage_body() -> tuple[int, str]:
    """`(status, body)` for `GET /`. The committed file, not a fresh render."""
    try:
        text = map_path().read_text(encoding="utf-8")
    except OSError:
        return 500, "coverage_map_missing\n"
    if not text.endswith("\n"):
        text += "\n"
    return 200, text


def bind(host: str, port: int) -> Server:
    return Server((host, port), Handler)


def run(args: argparse.Namespace) -> int:
    host = str(args.host).strip()
    port = int(args.port)
    if not host or any(char.isspace() for char in host):
        print("invalid_input: a host is required")
        return 1
    if port < 0 or port > 65535:
        print("invalid_input: a port is between 0 and 65535")
        return 1
    try:
        server = bind(host, port)
    except OSError:
        print("invalid_input: the address could not be bound")
        return 1
    raw_host, raw_port = server.server_address[:2]
    bound_host = raw_host.decode("ascii") if isinstance(raw_host, bytes) else raw_host
    print(f"listening: http://{bound_host}:{raw_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1", help="address to bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="port to bind (default 8080)")


class Handler(BaseHTTPRequestHandler):
    """Two paths. Anything else is `not_found`, and the request path is not echoed."""

    server_version = "wb"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        self._respond(include_body=True)

    def do_HEAD(self) -> None:
        self._respond(include_body=False)

    def _respond(self, *, include_body: bool) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/healthz":
            status, body = health_body()
        elif path == "/":
            status, body = coverage_body()
        else:
            status, body = 404, "not_found\n"
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", _TEXT)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        if include_body:
            self.wfile.write(data)

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        del size
        status = code if isinstance(code, int) else 0
        path = _token(self.path.split("?", 1)[0], limit=200)
        payload = {
            "event": "http",
            "method": _token(self.command, limit=16),
            "path": path,
            "status": status,
        }
        sys.stderr.write(json.dumps(payload, sort_keys=True) + "\n")

    def log_message(self, format: str, *args: Any) -> None:
        # `log_request` is the one line this server writes. The default interpolates
        # the request line, which a client can break across lines.
        del format, args


def _recorded_provider() -> ReplayProvider:
    return ReplayProvider.from_dict(
        {
            "replies": [
                {
                    "stop_reason": "end_turn",
                    "text": _RECORDED_TEXT,
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                }
            ]
        }
    )


def _token(value: str, *, limit: int = 64) -> str:
    cleaned = "".join(char for char in value if char.isprintable() and not char.isspace())
    return cleaned[:limit] or "none"
