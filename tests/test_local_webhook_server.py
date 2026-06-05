from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def _load_script_module(name: str, relative_path: str):
    script_path = Path(relative_path)
    spec = spec_from_file_location(name, script_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_local_webhook_server_returns_200_only_for_root(monkeypatch):
    monkeypatch.setenv("MAX_BOT_TOKEN", "token")
    monkeypatch.setenv("MAX_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("MAX_ENABLE_LONG_POLLING", "false")

    module = _load_script_module("local_webhook_server_script", "examples/local_webhook_server.py")
    handler = module.Handler.__new__(module.Handler)
    handler.path = "/.env"
    status_codes = []
    headers = []
    body = []
    handler.send_response = status_codes.append
    handler.send_header = lambda key, value: headers.append((key, value))
    handler.end_headers = lambda: None
    handler.wfile = type("Writer", (), {"write": body.append})()

    handler.do_GET()

    assert status_codes == [404]
    assert ("Content-Type", "text/plain") in headers
    assert body == [b"not found"]


def test_local_webhook_server_returns_200_for_root(monkeypatch):
    monkeypatch.setenv("MAX_BOT_TOKEN", "token")
    monkeypatch.setenv("MAX_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("MAX_ENABLE_LONG_POLLING", "false")

    module = _load_script_module("local_webhook_server_script_root", "examples/local_webhook_server.py")
    handler = module.Handler.__new__(module.Handler)
    handler.path = "/"
    status_codes = []
    headers = []
    body = []
    handler.send_response = status_codes.append
    handler.send_header = lambda key, value: headers.append((key, value))
    handler.end_headers = lambda: None
    handler.wfile = type("Writer", (), {"write": body.append})()

    handler.do_GET()

    assert status_codes == [200]
    assert ("Content-Type", "text/plain") in headers
    assert body == [b"ok"]


def test_local_webhook_server_logs_event_context(monkeypatch, capsys):
    monkeypatch.setenv("MAX_BOT_TOKEN", "token")
    monkeypatch.setenv("MAX_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("MAX_ENABLE_LONG_POLLING", "false")

    module = _load_script_module("local_webhook_server_script_post", "examples/local_webhook_server.py")
    payload = b'{"update_type":"message_created","message":{"recipient":{"chat_id":503998023},"sender":{"user_id":238627571},"body":{"text":"hello"}}}'
    handler = module.Handler.__new__(module.Handler)
    handler.path = "/"
    handler.headers = {"Content-Length": str(len(payload)), "X-Max-Bot-Api-Secret": "secret"}
    handler.rfile = type("Reader", (), {"read": lambda self, length: payload})()
    handler.wfile = type("Writer", (), {"write": lambda self, data: None})()
    handler.send_response = lambda status: None
    handler.send_header = lambda key, value: None
    handler.end_headers = lambda: None

    handler.do_POST()
    output = capsys.readouterr().out

    assert "POST / status=200" in output
    assert "event=message_created" in output
    assert "chat_id=503998023" in output
    assert "user_id=238627571" in output
