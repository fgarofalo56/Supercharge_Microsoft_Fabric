"""Exercise the setup HTTP handler with synthetic external services."""

import io
import json
from http.client import HTTPConnection
from http.server import HTTPServer
from threading import Thread
from unittest.mock import Mock

import app_setup
import pytest


@pytest.mark.parametrize("retry", [False, True])
def test_registration_http(monkeypatch, capsys, retry: bool) -> None:
    state = "test-session"
    code = "abcdefghij123"
    key = "synthetic-key"
    vault = Mock()
    if retry:
        vault.set_secret.side_effect = [RuntimeError(key), None, None]
    conversion = Mock(
        side_effect=lambda *a, **kw: io.BytesIO(
            json.dumps({"id": 123, "slug": "test-runner", "pem": key}).encode()
        )
    )
    monkeypatch.setattr(app_setup.secrets, "token_urlsafe", lambda size: state)
    monkeypatch.setattr(app_setup, "urlopen", conversion)
    server = HTTPServer(("127.0.0.1", 0), app_setup.BaseHTTPRequestHandler)
    port = server.server_port
    failures = []

    def factory(address, handler):
        assert address == ("127.0.0.1", port)
        server.RequestHandlerClass = handler
        return server

    monkeypatch.setattr(app_setup, "HTTPServer", factory)

    def run() -> None:
        try:
            app_setup.serve(vault, port)
        except BaseException as exc:
            failures.append(exc)

    thread = Thread(target=run, daemon=True)
    thread.start()

    def get(path: str, host: str | None = None):
        connection = HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            connection.request("GET", path, headers={"Host": host} if host else {})
            response = connection.getresponse()
            return (
                response.status,
                dict(response.getheaders()),
                response.read().decode(),
            )
        finally:
            connection.close()

    callback = f"/callback?state={state}&code={code}"
    try:
        assert get("/", "attacker.example")[0] == 403
        assert get("/")[0] == 404
        assert get("/callback?state=wrong&code=" + code)[0] == 403
        assert get(callback + "&code=" + code)[0] == 403
        conversion.assert_not_called()
        vault.set_secret.assert_not_called()
        status, headers, body = get("/?session=" + state)
        assert status == 200
        assert headers["Cache-Control"] == "no-store"
        assert headers["Referrer-Policy"] == "no-referrer"
        assert "https://github.com/settings/apps/new" in body
        if retry:
            status, _, body = get(callback)
            assert status == 502
            assert key not in body
        status, _, body = get(callback)
        assert status == 200
        assert "https://github.com/apps/test-runner/installations/new" in body
        assert key not in body
        conversion.assert_called_once()
        request = conversion.call_args.args[0]
        assert request.method == "POST"
        assert request.full_url.endswith(f"/{code}/conversions")
        assert vault.set_secret.call_args_list[-2].args == (
            "github-app-private-key",
            key,
        )
        assert vault.set_secret.call_args_list[-1].args == ("github-app-id", "123")
    finally:
        thread.join(timeout=2)
        if thread.is_alive():
            vault.set_secret.side_effect = None
            try:
                get(callback)
            except OSError:
                server.server_close()
            thread.join(timeout=3)
        server.server_close()
    assert not thread.is_alive()
    assert not failures
    output = capsys.readouterr()
    assert key not in output.out + output.err
    assert code not in output.out + output.err
