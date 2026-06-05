from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.client import build_answer_callback_request
from hermes_max_adapter.config import MaxAdapterConfig


class StubCallbackSender:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send(self, request: dict) -> dict:
        self.calls.append(request)
        return {"ok": True, "status_code": 200}


def build_config() -> MaxAdapterConfig:
    return MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )


def test_adapter_answer_callback_builds_vendor_request():
    adapter = MaxAdapter(config=build_config(), sender=StubCallbackSender())

    result = adapter.answer_callback_sync(callback_id="cb-1", text="done")

    assert result["success"] is True
    assert adapter.sender.calls[0]["url"] == "https://platform-api.max.ru/answers?callback_id=cb-1&message=done"
    assert adapter.sender.calls[0]["json"] == {}


def test_adapter_answer_callback_supports_notification_and_show_alert_fields():
    adapter = MaxAdapter(config=build_config(), sender=StubCallbackSender())

    result = adapter.answer_callback_sync(
        callback_id="cb-2",
        text="attention",
        notification="toast",
        show_alert=True,
    )

    assert result["success"] is True
    assert adapter.sender.calls[0]["url"] == "https://platform-api.max.ru/answers?callback_id=cb-2&message=attention"
    assert adapter.sender.calls[0]["json"] == {
        "notification": "toast",
        "show_alert": "true",
    }


def test_build_answer_callback_request_uses_notification_in_body_and_message_in_query():
    request = build_answer_callback_request(
        base_url="https://platform-api.max.ru",
        token="token",
        callback_id="cb-3",
        text="done",
        notification="toast",
        show_alert=False,
    )

    assert request["url"] == "https://platform-api.max.ru/answers?callback_id=cb-3&message=done"
    assert request["json"] == {
        "notification": "toast",
        "show_alert": "false",
    }
