from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.transport import HttpMaxSender


def test_http_sender_builds_request_with_timeout():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
        request_timeout_seconds=12,
    )
    sender = HttpMaxSender(config=config)
    request = sender.prepare_request(
        {
            "method": "POST",
            "url": "https://platform-api.max.ru/messages?chat_id=1",
            "headers": {"Authorization": "token", "Content-Type": "application/json"},
            "json": {"text": "hello"},
        }
    )
    assert request["timeout"] == 12
