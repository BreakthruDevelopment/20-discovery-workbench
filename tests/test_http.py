"""`GET /healthz`, `GET /api/health` and `GET /`."""

from __future__ import annotations

import http.client
import json
import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

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


def test_the_platform_health_path_serves_exactly_what_healthz_serves(
    server: tuple[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`/api/health` is the path the AWS deploy gate polls (issue #36).

    Both the status and the body are compared, not just "it answered 200": a second
    handler that drifted from `/healthz` would still satisfy a health poll, and the
    point of the alias is that there is one handler. The store and the source library
    are made to raise here too -- the platform path must be as cheap as `/healthz`,
    or a deploy gate that polls it every 10 seconds opens the database every time.
    """

    def boom(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("health must not touch the store or the sources")

    monkeypatch.setattr(Store, "open", boom)
    monkeypatch.setattr(SourceLibrary, "list_documents", boom)
    monkeypatch.setattr(SourceLibrary, "read", boom)
    monkeypatch.setattr(SourceLibrary, "for_engagement", boom)

    host, port = server
    answer = _get(host, port, http_mod._PLATFORM_HEALTH_PATH)
    assert answer == (200, f"version: {__version__}\nreplay: ok\nstop_reason: end_turn\n")
    assert _get(host, port, "/healthz") == answer

    connection = http.client.HTTPConnection(host, port, timeout=5)
    connection.request("HEAD", http_mod._PLATFORM_HEALTH_PATH)
    head = connection.getresponse()
    assert head.status == 200
    assert head.read() == b""
    connection.close()


@pytest.mark.parametrize(
    "near", ["/api", "/api/", "/api/health/", "/api/health/x", "/api/healthz", "/healthzz"]
)
def test_a_path_beside_the_health_paths_is_still_not_found(
    server: tuple[str, int], near: str
) -> None:
    """The routes are exact matches. A prefix test would answer every /api/... path.

    `/api/health/` is in the list on purpose: a trailing slash is the one neighbour a
    health checker might send, and it must behave like any other unknown path rather
    than like a third health route nothing pins.
    """
    host, port = server
    assert _get(host, port, near) == (404, "not_found\n")


def test_the_health_path_the_deploy_gate_polls_is_the_literal_it_polls() -> None:
    """The literal, not the constant. `30-apps-infra/deploy/aws.sh:336` curls this exact
    path for every app and has no per-app override, so the value is a contract with
    another repo rather than a choice this repo gets to make. Asserting the constant
    against itself -- which is what the assertions above do, deliberately, so that they
    read as being about the route -- holds for whatever the constant says. Same reason
    the unset-host test below writes `"0.0.0.0"` out in full.
    """
    assert http_mod._PLATFORM_HEALTH_PATH == "/api/health"
    assert frozenset({"/healthz", "/api/health"}) == http_mod._HEALTH_PATHS


def test_the_live_smoke_polls_the_path_the_deploy_gate_polls() -> None:
    """`scripts/smoke.sh --url` is the live check after a deploy (issue #36).

    It is not enough for the server to serve this path: the smoke has to poll it, or
    the smoke passes while the deploy itself records a failure on the same URL.

    Comment lines are dropped first and the whole invocation is matched: this change
    puts a comment block directly above the poll that names the path, so a substring
    search over the raw file would be satisfied by that comment alone with the poll
    moved elsewhere -- a test that cannot fail for the reason it exists.
    """
    script = (Path(__file__).resolve().parents[1] / "scripts" / "smoke.sh").read_text(
        encoding="utf-8"
    )
    live = [line.strip() for line in script.splitlines() if not line.strip().startswith("#")]
    assert (
        f'platform_health=$(curl -fsS --max-time 30 "$base{http_mod._PLATFORM_HEALTH_PATH}")'
        in live
    )


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


def test_the_host_defaults_to_every_interface_so_a_container_is_reachable() -> None:
    """127.0.0.1 inside a container has no client. This default is the deploy fix.

    The literal, not `http_mod._DEFAULT_HOST`: compared against the constant the function
    returns, this assertion holds for whatever that constant says and proves nothing.
    """
    assert http_mod.resolve_host(None, {}) == "0.0.0.0"  # noqa: S104 -- asserting the default


def test_an_explicit_host_beats_the_environment() -> None:
    assert http_mod.resolve_host("127.0.0.1", {"WB_HOST": "10.0.0.1"}) == "127.0.0.1"


def test_the_host_comes_from_the_environment_when_no_flag_is_given() -> None:
    assert http_mod.resolve_host(None, {"WB_HOST": "10.0.0.1"}) == "10.0.0.1"


@pytest.mark.parametrize("bad", ["", "   ", "a host", "\t"])
def test_a_blank_or_spaced_host_is_refused_rather_than_silently_replaced(bad: str) -> None:
    with pytest.raises(http_mod.ConfigError) as caught:
        http_mod.resolve_host(bad, {})
    assert caught.value.code == "invalid_input: a host is required"


def test_the_port_defaults_to_8080() -> None:
    assert http_mod.resolve_port(None, {}) == 8080


def test_the_port_comes_from_the_environment_because_the_platform_hands_it_over() -> None:
    assert http_mod.resolve_port(None, {"PORT": "9123"}) == 9123


def test_an_explicit_port_beats_the_environment() -> None:
    assert http_mod.resolve_port(443, {"PORT": "9123"}) == 443


def test_a_blank_port_variable_falls_back_rather_than_failing() -> None:
    """An empty PORT is an unset PORT, which is how a bare `docker run` arrives."""
    assert http_mod.resolve_port(None, {"PORT": "  "}) == 8080


@pytest.mark.parametrize("bad", ["eight", "80 80", "8080.0", "0x1f90", "٨٠٨٠"])
def test_a_malformed_port_variable_is_refused_and_not_echoed(bad: str) -> None:
    """Falling back to 8080 would bind somewhere the platform is not health-checking.

    `٨٠٨٠` is Arabic-Indic digits, which `int()` accepts and a port parser must not:
    the platform wrote `PORT` as ASCII or it meant something else.
    """
    with pytest.raises(http_mod.ConfigError) as caught:
        http_mod.resolve_port(None, {"PORT": bad})
    assert caught.value.code == "invalid_input: PORT is not a number"
    assert bad not in caught.value.code


@pytest.mark.parametrize("bad", ["70000", "-1", "65536"])
def test_a_port_variable_outside_the_range_is_refused(bad: str) -> None:
    with pytest.raises(http_mod.ConfigError) as caught:
        http_mod.resolve_port(None, {"PORT": bad})
    assert caught.value.code == "invalid_input: a port is between 0 and 65535"


def test_serve_refuses_a_malformed_port_variable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PORT", "not-a-port")
    assert main(["serve"]) == 1
    captured = capsys.readouterr()
    assert captured.out == "invalid_input: PORT is not a number\n"
    assert "not-a-port" not in captured.out


def test_a_malformed_port_variable_does_not_break_the_rest_of_the_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`PORT` is read in `run()`, not as an argparse default.

    `build_parser()` runs for every invocation, so resolving `PORT` there would make one
    bad variable in the deploy environment break `wb --version`, `wb sources list` and
    every other command along with `serve`.
    """
    monkeypatch.setenv("PORT", "not-a-port")
    with pytest.raises(SystemExit) as caught:
        main(["--version"])
    assert caught.value.code == 0
    assert capsys.readouterr().out == f"wb {__version__}\n"
