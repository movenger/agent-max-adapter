import json

from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.webhook_app import WebhookApplication


def test_webhook_app_rejects_invalid_secret():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    adapter = MaxAdapter(config=config)
    app = WebhookApplication(adapter=adapter, webhook_secret="secret")

    status, body = app.handle_request(headers={"X-Max-Bot-Api-Secret": "wrong"}, body=b"{}")

    assert status == 401
    assert body == b"unauthorized"


def test_webhook_app_accepts_valid_payload_and_dispatches():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    adapter = MaxAdapter(config=config)
    app = WebhookApplication(adapter=adapter, webhook_secret="secret")
    payload = {
        "update_type": "message_created",
        "chat_id": "c1",
        "user_id": "u1",
        "message": {"body": {"text": "hello"}},
        "mid": "m1",
    }

    status, body = app.handle_request(
        headers={"X-Max-Bot-Api-Secret": "secret"},
        body=json.dumps(payload).encode("utf-8"),
    )

    assert status == 200
    assert body == b"ok"
    assert adapter.health_status()["metrics"]["inbound_updates_total"] == 1
