"""`GET /healthz` and `GET /`."""

from __future__ import annotations

import http.client
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
