from pathlib import Path
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.env import load_project_env
from hermes_max_adapter.webhook_app import WebhookApplication


load_project_env(ROOT / ".env")
config = MaxAdapterConfig.from_env()
adapter = MaxAdapter(config=config)
app = WebhookApplication(adapter=adapter, webhook_secret=config.webhook_secret)


def _extract_event_context(body: bytes) -> tuple[str | None, str | None, str | None]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, None, None

    event_type = payload.get("update_type")
    message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
    recipient = message.get("recipient") if isinstance(message.get("recipient"), dict) else {}
    sender = message.get("sender") if isinstance(message.get("sender"), dict) else {}

    chat_id = recipient.get("chat_id")
    user_id = sender.get("user_id")
    return (
        str(event_type) if event_type is not None else None,
        str(chat_id) if chat_id is not None else None,
        str(user_id) if user_id is not None else None,
    )


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        status, response = app.handle_request(dict(self.headers), body)
        event_type, chat_id, user_id = _extract_event_context(body)
        print(
            f"POST {self.path} status={status} bytes={length}"
            f" event={event_type or '-'} chat_id={chat_id or '-'} user_id={user_id or '-'}",
            flush=True,
        )
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(response)

    def do_GET(self) -> None:  # noqa: N802
        print(f"GET {self.path}", flush=True)
        if self.path != "/":
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")


def main() -> None:
    port = int(os.getenv("LOCAL_WEBHOOK_PORT", "18080"))
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Local webhook server on http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
