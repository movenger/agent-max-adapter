from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.models.attachments import AttachmentKind, AttachmentRef, AttachmentSourceKind
from hermes_max_adapter.models.max_updates import (
    InboundEventEnvelope,
    InboundEventType,
    InboundMessage,
    MessageContentType,
)
from hermes_max_adapter.updates import normalize_update


def test_canonical_inbound_message_keeps_legacy_compatibility_properties():
    event = InboundEventEnvelope.message(
        vendor_event_name="message_created",
        chat_id="chat-1",
        user_id="user-1",
        message_id="msg-1",
        delivery_key="message_created:msg-1",
        payload=InboundMessage(
            content_type=MessageContentType.TEXT,
            text="hello",
            attachments=[],
        ),
    )

    assert event.event_type == InboundEventType.MESSAGE
    assert event.payload.content_type == MessageContentType.TEXT
    assert event.kind == "message"
    assert event.chat_id == "chat-1"
    assert event.user_id == "user-1"
    assert event.text == "hello"
    assert event.update_type == "message_created"


def test_canonical_inbound_message_can_carry_attachment_metadata():
    event = InboundEventEnvelope.message(
        vendor_event_name="message_created",
        chat_id="chat-9",
        user_id="user-9",
        message_id="msg-9",
        delivery_key="message_created:msg-9",
        payload=InboundMessage(
            content_type=MessageContentType.PHOTO,
            text=None,
            caption="look",
            attachments=[
                AttachmentRef(
                    kind=AttachmentKind.PHOTO,
                    source=AttachmentSourceKind.VENDOR_TOKEN,
                    upload_token="ph-1",
                )
            ],
        ),
    )

    assert event.payload.content_type == MessageContentType.PHOTO
    assert event.payload.caption == "look"
    assert event.payload.attachments[0].upload_token == "ph-1"
    assert event.text is None


def test_normalize_message_created_update():
    event = normalize_update(
        {
            "update_type": "message_created",
            "message": {"body": {"text": "hi"}},
            "chat_id": "chat-1",
            "user_id": "user-1",
        }
    )
    assert event.kind == "message"
    assert event.chat_id == "chat-1"
    assert event.user_id == "user-1"
    assert event.text == "hi"


def test_normalize_real_max_updates_shape_uses_snake_case_recipient_and_sender_fields():
    event = normalize_update(
        {
            "update_type": "message_created",
            "timestamp": 1780527862033,
            "user_locale": "ru",
            "marker": 4343,
            "message": {
                "recipient": {
                    "chat_id": 503998023,
                    "chat_type": "dialog",
                    "user_id": 271797428,
                },
                "timestamp": 1780527862033,
                "body": {
                    "mid": "mid.000000001e0a6647019e8fbb11113743",
                    "seq": 116688673966208835,
                    "text": "Эй",
                },
                "sender": {
                    "user_id": 238627571,
                    "first_name": "Денис",
                    "last_name": "",
                    "is_bot": False,
                    "last_activity_time": 1780527862000,
                    "name": "Денис",
                },
            },
        }
    )

    assert event.kind == "message"
    assert event.chat_id == "503998023"
    assert event.user_id == "238627571"
    assert event.message_id == "mid.000000001e0a6647019e8fbb11113743"
    assert event.text == "Эй"
    assert event.payload.metadata["marker"] == 4343
    assert event.payload.metadata["recipient_user_id"] == 271797428


def test_normalize_live_message_created_shape():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "body": {"text": "hello from live"},
                    "sender": {"userId": "user-42"},
                    "recipient": {"chatId": "chat-42"},
                    "mid": "mid-42",
                }
            },
        }
    )
    assert event.kind == "message"
    assert event.chat_id == "chat-42"
    assert event.user_id == "user-42"
    assert event.text == "hello from live"
    assert event.update_type == "message_created"


def test_normalize_live_message_with_photo_attachment_classifies_photo_content():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "body": {"text": "caption text"},
                    "sender": {"userId": "user-42"},
                    "recipient": {"chatId": "chat-42"},
                    "mid": "mid-photo-1",
                    "attachments": [{"type": "image", "photoToken": "ph-1"}],
                }
            },
        }
    )

    assert event.kind == "message"
    assert event.payload.content_type == MessageContentType.PHOTO
    assert event.payload.caption == "caption text"
    assert event.payload.attachments[0].kind == AttachmentKind.PHOTO
    assert event.payload.attachments[0].upload_token == "ph-1"


def test_normalize_live_message_with_video_attachment_classifies_video_content():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "body": {"text": "video caption"},
                    "sender": {"userId": "user-52"},
                    "recipient": {"chatId": "chat-52"},
                    "mid": "mid-video-1",
                    "attachments": [{"type": "video", "videoToken": "vid-1"}],
                }
            },
        }
    )

    assert event.payload.content_type == MessageContentType.VIDEO
    assert event.payload.caption == "video caption"
    assert event.payload.attachments[0].kind == AttachmentKind.VIDEO
    assert event.payload.attachments[0].upload_token == "vid-1"


def test_normalize_live_message_with_document_attachment_classifies_document_content():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "body": {"text": "doc caption"},
                    "sender": {"userId": "user-62"},
                    "recipient": {"chatId": "chat-62"},
                    "mid": "mid-doc-1",
                    "attachments": [{"type": "file", "fileToken": "doc-1", "fileName": "a.pdf"}],
                }
            },
        }
    )

    assert event.payload.content_type == MessageContentType.DOCUMENT
    assert event.payload.caption == "doc caption"
    assert event.payload.attachments[0].kind == AttachmentKind.DOCUMENT
    assert event.payload.attachments[0].upload_token == "doc-1"


def test_normalize_live_message_with_audio_attachment_classifies_audio_content():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "body": {"text": "audio caption"},
                    "sender": {"userId": "user-72"},
                    "recipient": {"chatId": "chat-72"},
                    "mid": "mid-audio-1",
                    "attachments": [{"type": "audio", "audioToken": "aud-1"}],
                }
            },
        }
    )

    assert event.payload.content_type == MessageContentType.AUDIO
    assert event.payload.caption == "audio caption"
    assert event.payload.attachments[0].kind == AttachmentKind.AUDIO
    assert event.payload.attachments[0].upload_token == "aud-1"


def test_normalize_live_message_with_voice_attachment_classifies_voice_content():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "body": {"text": "voice caption"},
                    "sender": {"userId": "user-82"},
                    "recipient": {"chatId": "chat-82"},
                    "mid": "mid-voice-1",
                    "attachments": [{"type": "voice", "voiceToken": "voc-1"}],
                }
            },
        }
    )

    assert event.payload.content_type == MessageContentType.VOICE
    assert event.payload.caption == "voice caption"
    assert event.payload.attachments[0].kind == AttachmentKind.VOICE
    assert event.payload.attachments[0].upload_token == "voc-1"


def test_normalize_live_message_with_sticker_attachment_classifies_sticker_content():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "sender": {"userId": "user-92"},
                    "recipient": {"chatId": "chat-92"},
                    "mid": "mid-sticker-1",
                    "attachments": [{"type": "sticker", "stickerToken": "st-1"}],
                }
            },
        }
    )

    assert event.payload.content_type == MessageContentType.STICKER
    assert event.payload.attachments[0].kind == AttachmentKind.STICKER
    assert event.payload.attachments[0].upload_token == "st-1"


def test_normalize_live_message_with_animation_attachment_classifies_animation_content():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "body": {"text": "gif caption"},
                    "sender": {"userId": "user-102"},
                    "recipient": {"chatId": "chat-102"},
                    "mid": "mid-gif-1",
                    "attachments": [{"type": "animation", "animationToken": "gif-1"}],
                }
            },
        }
    )

    assert event.payload.content_type == MessageContentType.ANIMATION
    assert event.payload.caption == "gif caption"
    assert event.payload.attachments[0].kind == AttachmentKind.ANIMATION
    assert event.payload.attachments[0].upload_token == "gif-1"


def test_normalize_live_message_with_contact_attachment_classifies_contact_content():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "body": {"text": "share contact"},
                    "sender": {"userId": "user-112"},
                    "recipient": {"chatId": "chat-112"},
                    "mid": "mid-contact-1",
                    "attachments": [
                        {
                            "type": "contact",
                            "name": "Denis",
                            "phone": "+799****0000",
                        }
                    ],
                }
            },
        }
    )

    assert event.payload.content_type == MessageContentType.CONTACT
    assert event.payload.caption == "share contact"
    assert event.payload.attachments[0].kind == AttachmentKind.CONTACT
    assert event.payload.attachments[0].metadata["name"] == "Denis"
    assert event.payload.attachments[0].metadata["phone"] == "+799****0000"


def test_normalize_live_message_with_location_attachment_classifies_location_content():
    event = normalize_update(
        {
            "eventType": "messageCreated",
            "messageCreated": {
                "message": {
                    "body": {"text": "share pin"},
                    "sender": {"userId": "user-122"},
                    "recipient": {"chatId": "chat-122"},
                    "mid": "mid-location-1",
                    "attachments": [
                        {
                            "type": "location",
                            "latitude": 55.75,
                            "longitude": 37.61,
                        }
                    ],
                }
            },
        }
    )

    assert event.payload.content_type == MessageContentType.LOCATION
    assert event.payload.caption == "share pin"
    assert event.payload.attachments[0].kind == AttachmentKind.LOCATION
    assert event.payload.attachments[0].metadata["latitude"] == 55.75
    assert event.payload.attachments[0].metadata["longitude"] == 37.61


def test_normalize_message_callback_update():
    event = normalize_update(
        {
            "update_type": "message_callback",
            "callback": {
                "id": "cb-1",
                "payload": "go:1",
                "user": {"user_id": "user-7"},
                "chat_id": "chat-7",
                "message": {"mid": "msg-7"},
            },
        }
    )

    assert event.event_type == InboundEventType.CALLBACK
    assert event.kind == "callback"
    assert event.chat_id == "chat-7"
    assert event.user_id == "user-7"
    assert event.payload.data == "go:1"
    assert event.payload.callback_id == "cb-1"
    assert event.payload.origin_message_id == "msg-7"


def test_normalize_bot_started_update_becomes_service_event():
    event = normalize_update(
        {
            "update_type": "bot_started",
            "chat_id": "chat-8",
            "user_id": "user-8",
        }
    )

    assert event.event_type == InboundEventType.SERVICE
    assert event.kind == "service"
    assert event.payload.service_type == "bot_started"
    assert event.chat_id == "chat-8"
    assert event.user_id == "user-8"


def test_normalize_unknown_update_becomes_unsupported():
    event = normalize_update({"update_type": "something_new", "chat_id": "c", "user_id": "u"})
    assert event.kind == "unsupported"
    assert event.chat_id == "c"
    assert event.user_id == "u"
    assert event.text is None


def build_config() -> MaxAdapterConfig:
    return MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )


def test_build_dedupe_key_uses_body_mid_for_real_max_shape():
    adapter = MaxAdapter(config=build_config())

    dedupe_key = adapter.build_dedupe_key(
        {
            "update_type": "message_created",
            "message": {
                "recipient": {"chat_id": 503998023},
                "body": {"mid": "mid.000000001e0a6647019e8fbb11113743", "text": "Эй"},
                "sender": {"user_id": 238627571},
            },
        }
    )

    assert dedupe_key == "message_created:mid.000000001e0a6647019e8fbb11113743"


def test_process_update_real_max_shape_duplicate_delivery_is_ignored():
    adapter = MaxAdapter(config=build_config())
    payload = {
        "update_type": "message_created",
        "marker": 4343,
        "message": {
            "recipient": {"chat_id": 503998023, "chat_type": "dialog", "user_id": 271797428},
            "body": {"mid": "mid.000000001e0a6647019e8fbb11113743", "seq": 116688673966208835, "text": "Эй"},
            "sender": {"user_id": 238627571, "first_name": "Денис", "name": "Денис"},
        },
    }

    first = adapter.process_update(payload)
    second = adapter.process_update(payload)

    assert first["dedupe"] == "accepted"
    assert first["event"] is not None
    assert first["event"].kind == "message"
    assert first["event"].chat_id == "503998023"
    assert first["event"].user_id == "238627571"
    assert second["dedupe"] == "duplicate"
    assert second["event"] is None


def test_process_update_live_shape_duplicate_delivery_is_ignored():
    adapter = MaxAdapter(config=build_config())
    payload = {
        "eventType": "messageCreated",
        "messageCreated": {
            "message": {
                "body": {"text": "hello from live"},
                "sender": {"userId": "user-42"},
                "recipient": {"chatId": "chat-42"},
                "mid": "mid-42",
            }
        },
    }

    first = adapter.process_update(payload)
    second = adapter.process_update(payload)

    assert first["dedupe"] == "accepted"
    assert first["event"] is not None
    assert first["event"].kind == "message"
    assert first["event"].text == "hello from live"
    assert second["dedupe"] == "duplicate"
    assert second["event"] is None
