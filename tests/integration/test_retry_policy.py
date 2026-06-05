from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig


class AlwaysFailSender:
    def __init__(self) -> None:
        self.calls = 0

    def send(self, request: dict) -> dict:
        self.calls += 1
        return {"status_code": 503, "error": "service unavailable"}


def test_adapter_respects_configured_max_retries():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
        max_retries=3,
        retry_backoff_seconds=0.0,
    )
    sender = AlwaysFailSender()
    adapter = MaxAdapter(config=config, sender=sender)

    result = adapter.send_text_sync(chat_id="1", text="hello")

    assert result["success"] is False
    assert sender.calls == 4
    assert result["failures"][0]["attempts"] == 4
