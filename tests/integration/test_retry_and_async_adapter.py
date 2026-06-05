import asyncio
import os

from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.client import build_send_request
from hermes_max_adapter.config import MaxAdapterConfig


class FlakySender:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._count = 0

    def send(self, request: dict) -> dict:
        self.calls.append(request)
        self._count += 1
        if self._count == 1:
            return {"status_code": 429, "error": "rate limited"}
        return {"status_code": 200, "message_id": f"msg-{self._count}"}


def test_adapter_retries_retryable_failure_and_succeeds():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    sender = FlakySender()
    adapter = MaxAdapter(config=config, sender=sender)

    result = adapter.send_text_sync(chat_id="1", text="hello")

    assert result["success"] is True
    assert result["message_ids"] == ["msg-2"]
    assert len(sender.calls) == 2


def test_async_send_matches_sync_success_path():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )

    class Sender:
        def send(self, request: dict) -> dict:
            return {"status_code": 200, "message_id": "m1"}

    adapter = MaxAdapter(config=config, sender=Sender())
    result = asyncio.run(adapter.send(chat_id="1", content="hello"))
    assert result["success"] is True
    assert result["message_ids"] == ["m1"]


def test_send_text_to_user_sync_prefers_resolved_chat_id_but_falls_back_to_user_id_only():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )

    class Sender:
        def __init__(self) -> None:
            self.calls = []

        def send(self, request: dict) -> dict:
            self.calls.append(request)
            return {"status_code": 200, "message_id": "m2"}

    adapter = MaxAdapter(config=config, sender=Sender())

    first = adapter.send_text_to_user_sync(user_id="238627571", text="before dialog")
    adapter.process_update(
        {
            "update_type": "message_created",
            "marker": 4343,
            "message": {
                "recipient": {"chat_id": 503998023, "chat_type": "dialog", "user_id": 271797428},
                "body": {"mid": "mid.000000001e0a6647019e8fbb11113743", "seq": 116688673966208835, "text": "Эй"},
                "sender": {"user_id": 238627571, "first_name": "Денис", "name": "Денис"},
            },
        }
    )
    second = adapter.send_text_to_user_sync(user_id="238627571", text="after dialog")

    assert first["success"] is True
    assert second["success"] is True
    assert adapter.sender.calls[0]["url"] == "https://platform-api.max.ru/messages?user_id=238627571"
    assert adapter.sender.calls[1]["url"] == "https://platform-api.max.ru/messages?user_id=238627571&chat_id=503998023"


def test_send_text_to_user_sync_uses_user_id_targeting():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )

    class Sender:
        def __init__(self) -> None:
            self.calls = []

        def send(self, request: dict) -> dict:
            self.calls.append(request)
            return {"status_code": 200, "message_id": "m2"}

    adapter = MaxAdapter(config=config, sender=Sender())
    result = adapter.send_text_to_user_sync(user_id="238627571", text="hello")
    assert result["success"] is True
    assert adapter.sender.calls[0]["url"] == "https://platform-api.max.ru/messages?user_id=238627571"


def test_build_send_request_allows_user_id_with_resolved_chat_id():
    request = build_send_request(
        base_url="https://platform-api.max.ru",
        token="token",
        user_id="238627571",
        chat_id="503998023",
        payload={"text": "hello"},
    )

    assert request["url"] == "https://platform-api.max.ru/messages?user_id=238627571&chat_id=503998023"


def test_config_reads_bot_token_from_env_file_environment(monkeypatch):
    monkeypatch.setenv("MAX_BOT_TOKEN", "env-token")
    monkeypatch.setenv("MAX_WEBHOOK_SECRET", "env-secret")
    monkeypatch.setenv("MAX_ENABLE_LONG_POLLING", "false")

    config = MaxAdapterConfig.from_env()

    assert config.bot_token == "env-token"
    assert config.webhook_secret == "env-secret"


def test_repo_env_file_contains_max_bot_token_for_live_smoke():
    env_path = "/home/hype/workspaces/hermes-max-adapter/.env"
    assert os.path.exists(env_path)
    with open(env_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    assert "MAX_BOT_TOKEN=" in content
