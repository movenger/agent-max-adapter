from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.dedupe import DedupeDecision


def test_adapter_process_update_returns_duplicate_for_repeated_event():
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
    first = adapter.process_update(payload)
    second = adapter.process_update(payload)

    assert first["dedupe"] == DedupeDecision.ACCEPTED
    assert first["event"].text == "hello"
    assert second["dedupe"] == DedupeDecision.DUPLICATE
    assert second["event"] is None
