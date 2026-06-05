from __future__ import annotations

import json

from hermes_max_adapter.webhook_server import dispatch_webhook_to_adapter, validate_secret


class WebhookApplication:
    def __init__(self, adapter: object, webhook_secret: str) -> None:
        self.adapter = adapter
        self.webhook_secret = webhook_secret

    def handle_request(self, headers: dict[str, str], body: bytes) -> tuple[int, bytes]:
        provided_secret = headers.get("X-Max-Bot-Api-Secret")
        if not validate_secret(self.webhook_secret, provided_secret):
            return 401, b"unauthorized"

        payload = json.loads(body.decode("utf-8"))
        dispatch_webhook_to_adapter(self.adapter, payload)
        return 200, b"ok"
