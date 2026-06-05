from hermes_max_adapter.webhook_server import dispatch_webhook_to_adapter
from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.dedupe import DedupeDecision


def test_dispatch_webhook_to_adapter_returns_accepted_event():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    adapter = MaxAdapter(config=config)
    payload = {
        "update_type": "message_created",
        "chat_id": "c1",
        "user_id": "u1",
        "message": {"body": {"text": "hello"}},
        "mid": "m1",
    }

    result = dispatch_webhook_to_adapter(adapter, payload)

    assert result["dedupe"] == DedupeDecision.ACCEPTED
    assert result["event"].text == "hello"


def test_dispatch_webhook_to_adapter_returns_duplicate_on_replay():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    adapter = MaxAdapter(config=config)
    payload = {
        "update_type": "message_created",
        "chat_id": "c1",
        "user_id": "u1",
        "message": {"body": {"text": "hello"}},
        "mid": "m1",
    }

    dispatch_webhook_to_adapter(adapter, payload)
    replay = dispatch_webhook_to_adapter(adapter, payload)

    assert replay["dedupe"] == DedupeDecision.DUPLICATE
    assert replay["event"] is None
