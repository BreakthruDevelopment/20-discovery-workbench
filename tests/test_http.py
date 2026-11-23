"""`GET /healthz` and `GET /`."""

from __future__ import annotations

import http.client
import json
import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterator

import pytest
from agent_container.core.messages import ModelRequest, ModelResponse
from agent_container.core.provider import ModelProvider

from workbench import __version__
from workbench.cli import http as http_mod
from workbench.cli import main
from workbench.cli.coverage import map_path
from workbench.core.sources import SourceLibrary
from workbench.core.store import Store


class _OtherStop(ModelProvider):
    """A replay that ends for a reason other than the recorded end_turn."""

    async def converse(self, request: ModelRequest) -> ModelResponse:
        del request
        return ModelResponse.of("nope", stop_reason="max_tokens")


def test_the_replay_round_trip_rejects_a_different_stop() -> None:
    ok, stop = http_mod.replay_round_trip(_OtherStop())
    assert ok is False
    assert stop == "max_tokens"


def test_health_body_is_the_version_and_a_passing_replay() -> None:
    status, body = http_mod.health_body()
    assert status == 200
    assert body == f"version: {__version__}\nreplay: ok\nstop_reason: end_turn\n"


def test_health_body_reports_a_failed_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http_mod, "replay_round_trip", lambda: (False, "max_tokens"))
    status, body = http_mod.health_body()
    assert status == 500
    assert "replay: failed\n" in body
    assert "stop_reason: max_tokens\n" in body
    assert "version: " in body


def test_the_coverage_body_is_the_committed_file() -> None:
    status, body = http_mod.coverage_body()
    assert status == 200
    assert body == map_path().read_text(encoding="utf-8")
    assert "1.2\t" in body
    assert "5.6\t" in body


@pytest.fixture
def server() -> Iterator[tuple[str, int]]:
    bound = http_mod.bind("127.0.0.1", 0)
    thread = threading.Thread(target=bound.serve_forever, daemon=True)
    thread.start()
    address = bound.server_address
    host, port = str(address[0]), int(address[1])
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.02)
    else:
        bound.shutdown()
        bound.server_close()
        raise AssertionError("the server did not accept a connection")
    try:
        yield host, port
    finally:
        bound.shutdown()
        bound.server_close()
        thread.join(timeout=5)


def _get(host: str, port: int, path: str) -> tuple[int, str]:
    url = f"http://{host}:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return int(response.status), response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8")


def test_the_server_serves_health_and_the_map_and_hides_other_paths(
    server: tuple[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Health does not open the store or the source library. Other paths are not echoed."""

    def boom(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("health must not touch the store or the sources")

    monkeypatch.setattr(Store, "open", boom)
    monkeypatch.setattr(SourceLibrary, "list_documents", boom)
    monkeypatch.setattr(SourceLibrary, "read", boom)
    monkeypatch.setattr(SourceLibrary, "for_engagement", boom)

    host, port = server
    status, body = _get(host, port, "/healthz")
    assert status == 200
    assert body == f"version: {__version__}\nreplay: ok\nstop_reason: end_turn\n"

    status, page = _get(host, port, "/")
    assert status == 200
    assert page == map_path().read_text(encoding="utf-8")

    marker = "/marker-do-not-echo"
    status, missing = _get(host, port, marker)
    assert status == 404
    assert missing == "not_found\n"
    assert marker not in missing

    connection = http.client.HTTPConnection(host, port, timeout=5)
    connection.request("HEAD", "/healthz")
    head = connection.getresponse()
    assert head.status == 200
    assert head.read() == b""
    connection.close()


def test_serve_rejects_a_port_outside_the_range(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["serve", "--port", "70000"]) == 1
    captured = capsys.readouterr()
    assert "invalid_input" in captured.out
    assert "70000" not in captured.out


def _raw(host: str, port: int, request: bytes, *, timeout: float = 5.0) -> bytes:
    """One raw request on a socket. `http.client` will not send a malformed request line."""
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(request)
        sock.settimeout(timeout)
        chunks: list[bytes] = []
        while True:
            try:
                chunk = sock.recv(4096)
            except OSError:
                break
            if not chunk:
                break
            chunks.append(chunk)
    return b"".join(chunks)


def test_a_malformed_request_line_still_gets_a_response(
    server: tuple[str, int], capsys: pytest.CaptureFixture[str]
) -> None:
    """`self.path` does not exist until `parse_request()` succeeds.

    `send_error` calls `send_response` calls `log_request`, which read `self.path` and
    raised `AttributeError` -- leaving the status line buffered and never flushed, so the
    client received **zero bytes** instead of a 400, and the traceback went to stderr and
    broke the one-JSON-line-per-request log contract. One line of input, unauthenticated,
    repeatable.
    """
    host, port = server
    capsys.readouterr()
    response = _raw(host, port, b"GET /CANARY-IN-REQUEST-LINE HTTP/9.9\r\n\r\n")
    assert response, "the client received no bytes at all"
    # 505, not 400: `parse_request()` rejects the version before the path, which is the
    # status this handler is handed. What matters is that a complete response arrives.
    assert response.startswith(b"HTTP/1.1 505 ")
    assert b"http_version_not_supported\n" in response
    # Nothing from the request line comes back, and the log is still one JSON line.
    assert b"CANARY-IN-REQUEST-LINE" not in response
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
    lines = [line for line in captured.err.splitlines() if line.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0])["event"] == "http"


def test_an_unparseable_request_line_is_not_echoed(server: tuple[str, int]) -> None:
    host, port = server
    response = _raw(host, port, b"BOGUS\xff CANARY2 JUNK\r\n\r\n")
    assert response.startswith(b"HTTP/1.1 400 ")
    assert b"CANARY2" not in response


def test_an_unsupported_method_is_not_echoed(server: tuple[str, int]) -> None:
    """The base class puts `self.command` in the reason phrase *and* in an HTML body.

    That is parsed request input in a response, on a surface whose only declared content
    type is text/plain -- the app 17 defect class, six routes over five rounds.
    """
    host, port = server
    canary = b"CANARYMETHOD"
    response = _raw(host, port, canary + b" / HTTP/1.1\r\nHost: localhost\r\n\r\n")
    assert response.startswith(b"HTTP/1.1 405 ")
    assert b"method_not_allowed\n" in response
    assert canary not in response
    # And the content type stays the only one this surface declares.
    assert b"text/html" not in response.lower()
    assert b"text/plain" in response.lower()


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH", "OPTIONS", "TRACE"])
def test_every_other_verb_is_a_fixed_plain_text_405(server: tuple[str, int], method: str) -> None:
    host, port = server
    response = _raw(host, port, f"{method} /healthz HTTP/1.1\r\nHost: localhost\r\n\r\n".encode())
    assert response.startswith(b"HTTP/1.1 405 ")
    assert b"method_not_allowed\n" in response
    assert b"text/html" not in response.lower()


def test_healthz_is_wired_to_the_real_round_trip(
    server: tuple[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The route must call the round-trip, not merely report a version.

    Replacing `replay_round_trip` with a constant success left every test passing, so
    nothing pinned that `/healthz` depends on the loop at all. This drives the recorded
    provider instead: a provider whose reply stops for any other reason is a failed
    round-trip and a 500, which is the whole point of the endpoint.
    """

    class _OtherStop(ModelProvider):
        async def converse(self, request: ModelRequest) -> ModelResponse:
            del request
            return ModelResponse.of(http_mod._RECORDED_TEXT, stop_reason="max_tokens")

    monkeypatch.setattr(http_mod, "_recorded_provider", _OtherStop)
    host, port = server
    status, body = _get(host, port, "/healthz")
    assert status == 500
    assert "replay: failed\n" in body
