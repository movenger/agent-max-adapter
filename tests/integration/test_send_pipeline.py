from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.client import build_send_request
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.models.actions import ActionButton, ActionButtonKind
from hermes_max_adapter.models.attachments import AttachmentKind, AttachmentRef, AttachmentSourceKind
from hermes_max_adapter.models.max_messages import OutboundActionRowPart, OutboundAttachmentPart, OutboundMessage, OutboundTextPart


class StubSender:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send(self, request: dict) -> dict:
        self.calls.append(request)
        return {"ok": True, "message_id": "msg-1", "status_code": 200}


def test_adapter_send_text_renders_and_sends_single_message():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    sender = StubSender()
    adapter = MaxAdapter(config=config, sender=sender)

    result = adapter.send_text_sync(chat_id="1", text="hello")

    assert result["success"] is True
    assert result["message_ids"] == ["msg-1"]
    assert sender.calls[0]["url"] == "https://platform-api.max.ru/messages?chat_id=1"
    assert sender.calls[0]["json"] == {"text": "hello"}


def test_adapter_indexes_real_dialog_from_update_and_prefers_user_id_targeting():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    sender = StubSender()
    adapter = MaxAdapter(config=config, sender=sender)

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

    result = adapter.send_message_sync(
        OutboundMessage(target_user_id="238627571", parts=[OutboundTextPart(text="hello user")])
    )

    assert result["success"] is True
    assert sender.calls[-1]["url"] == "https://platform-api.max.ru/messages?user_id=238627571&chat_id=503998023"
    assert sender.calls[-1]["json"] == {"text": "hello user"}
    request = build_send_request(
        base_url="https://platform-api.max.ru",
        token="token",
        user_id="238627571",
        chat_id="503998023",
        payload={"text": "hello user"},
    )
    assert request["url"] == sender.calls[-1]["url"]


def test_adapter_send_canonical_message_with_button_markup():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    sender = StubSender()
    adapter = MaxAdapter(config=config, sender=sender)

    result = adapter.send_message_sync(
        OutboundMessage(
            target_chat_id="1",
            parts=[
                OutboundTextPart(text="choose"),
                OutboundActionRowPart(
                    rows=[[ActionButton(kind=ActionButtonKind.CALLBACK, text="Go", payload="go:1")]]
                ),
            ],
        )
    )

    assert result["success"] is True
    assert result["message_ids"] == ["msg-1"]
    assert sender.calls[0]["json"] == {
        "text": "choose",
        "attachments": [
            {"type": "inline_keyboard", "payload": {"buttons": [[{"type": "callback", "text": "Go", "payload": "go:1"}]]}}
        ],
    }


def test_adapter_send_canonical_message_with_media_tokens():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    sender = StubSender()
    adapter = MaxAdapter(config=config, sender=sender)

    result = adapter.send_message_sync(
        OutboundMessage(
            target_chat_id="1",
            parts=[
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.PHOTO, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="ph-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.VIDEO, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="vid-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.DOCUMENT, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="doc-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.AUDIO, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="aud-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.VOICE, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="voc-1")),
            ],
        )
    )

    assert result["success"] is True
    assert sender.calls[0]["json"] == {
        "attachments": [
            {"type": "image", "payload": {"token": "ph-1"}},
            {"type": "video", "payload": {"token": "vid-1"}},
            {"type": "file", "payload": {"token": "doc-1"}},
            {"type": "audio", "payload": {"token": "aud-1"}},
        ],
        "voice": "voc-1",
    }


def test_adapter_send_canonical_message_with_sticker_animation_contact_and_location():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    sender = StubSender()
    adapter = MaxAdapter(config=config, sender=sender)

    result = adapter.send_message_sync(
        OutboundMessage(
            target_chat_id="1",
            parts=[
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.STICKER, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="st-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.ANIMATION, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="gif-1")),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.CONTACT, source=AttachmentSourceKind.VENDOR_PAYLOAD, metadata={"name": "Denis", "phone": "+799****0000"})),
                OutboundAttachmentPart(attachment=AttachmentRef(kind=AttachmentKind.LOCATION, source=AttachmentSourceKind.VENDOR_PAYLOAD, metadata={"latitude": 55.75, "longitude": 37.61})),
            ],
        )
    )

    actual = sender.calls[0]["json"]
    assert result["success"] is True
    assert actual["sticker"] == "st-1"
    assert actual["animation"] == "gif-1"
    assert actual["contact"]["name"] == "Denis"
    assert actual["contact"]["phone"] == "+799****0000"
    assert actual["location"] == {"latitude": 55.75, "longitude": 37.61}


def test_adapter_send_text_splits_long_message_into_multiple_requests():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    sender = StubSender()
    adapter = MaxAdapter(config=config, sender=sender)

    text = "a" * 9001
    result = adapter.send_text_sync(chat_id="1", text=text)

    assert result["success"] is True
    assert len(sender.calls) == 3
    assert len(result["message_ids"]) == 3
