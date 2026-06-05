from __future__ import annotations

from hermes_max_adapter.models.attachments import AttachmentKind, AttachmentRef, AttachmentSourceKind
from hermes_max_adapter.models.max_updates import (
    InboundCallback,
    InboundEventEnvelope,
    InboundEventType,
    InboundMessage,
    InboundServiceEvent,
    MessageContentType,
    NormalizedEvent,
)


def _extract_live_message(payload: dict) -> dict:
    return payload.get("messageCreated", {}).get("message", {})


def _resolve_recipient_chat_id(message: dict, payload: dict) -> str:
    recipient = message.get("recipient", {})
    return str(
        payload.get("chat_id")
        or recipient.get("chat_id")
        or recipient.get("chatId")
        or ""
    )


def _resolve_sender_user_id(message: dict, payload: dict) -> str:
    sender = message.get("sender", {})
    return str(
        payload.get("user_id")
        or sender.get("user_id")
        or sender.get("userId")
        or ""
    )


def _resolve_message_id(message: dict, payload: dict, live_message: dict) -> str | None:
    body = message.get("body", {})
    return str(
        body.get("mid")
        or message.get("mid")
        or payload.get("mid")
        or live_message.get("mid")
        or ""
    ) or None


def _resolve_update_type(payload: dict) -> str:
    update_type = payload.get("update_type")
    if update_type:
        return str(update_type)

    event_type = payload.get("eventType")
    if event_type == "messageCreated":
        return "message_created"
    return str(event_type or "unknown")


def _build_delivery_key(update_type: str, payload: dict, live_message: dict) -> str:
    callback = payload.get("callback", {})
    marker = (
        payload.get("mid")
        or payload.get("message", {}).get("mid")
        or live_message.get("mid")
        or callback.get("id")
        or payload.get("callback_id")
        or "unknown"
    )
    return f"{update_type}:{marker}"


def _classify_message_content(message: dict) -> tuple[MessageContentType, list[AttachmentRef], str | None, str | None]:
    attachments = message.get("attachments") or []
    text = message.get("body", {}).get("text")
    if not attachments:
        return MessageContentType.TEXT, [], text, None

    first = attachments[0]
    attachment_type = first.get("type")
    mapping: dict[str, tuple[MessageContentType, AttachmentKind, str | None, dict | None]] = {
        "image": (MessageContentType.PHOTO, AttachmentKind.PHOTO, first.get("photoToken"), None),
        "video": (MessageContentType.VIDEO, AttachmentKind.VIDEO, first.get("videoToken"), None),
        "file": (MessageContentType.DOCUMENT, AttachmentKind.DOCUMENT, first.get("fileToken"), None),
        "audio": (MessageContentType.AUDIO, AttachmentKind.AUDIO, first.get("audioToken"), None),
        "voice": (MessageContentType.VOICE, AttachmentKind.VOICE, first.get("voiceToken"), None),
        "sticker": (MessageContentType.STICKER, AttachmentKind.STICKER, first.get("stickerToken"), None),
        "animation": (MessageContentType.ANIMATION, AttachmentKind.ANIMATION, first.get("animationToken"), None),
        "contact": (
            MessageContentType.CONTACT,
            AttachmentKind.CONTACT,
            None,
            {"name": first.get("name"), "phone": first.get("phone")},
        ),
        "location": (
            MessageContentType.LOCATION,
            AttachmentKind.LOCATION,
            None,
            {"latitude": first.get("latitude"), "longitude": first.get("longitude")},
        ),
    }
    if attachment_type in mapping:
        content_type, attachment_kind, token, extra_metadata = mapping[attachment_type]
        metadata = {"raw_attachment": first}
        if extra_metadata:
            metadata.update({key: value for key, value in extra_metadata.items() if value is not None})
        return (
            content_type,
            [
                AttachmentRef(
                    kind=attachment_kind,
                    source=AttachmentSourceKind.VENDOR_TOKEN if token is not None else AttachmentSourceKind.VENDOR_PAYLOAD,
                    upload_token=token,
                    file_name=first.get("fileName"),
                    metadata=metadata,
                )
            ],
            None if attachment_type != "sticker" else None,
            text,
        )

    return MessageContentType.UNKNOWN, [], text, None


def normalize_update(payload: dict) -> NormalizedEvent:
    update_type = _resolve_update_type(payload)
    live_message = _extract_live_message(payload)
    if update_type == "message_created":
        message = payload.get("message") or live_message
        chat_id = _resolve_recipient_chat_id(message, payload)
        user_id = _resolve_sender_user_id(message, payload)
        content_type, attachments, text, caption = _classify_message_content(message)
        recipient = message.get("recipient", {})
        return InboundEventEnvelope.message(
            vendor_event_name=update_type,
            chat_id=chat_id,
            user_id=user_id,
            message_id=_resolve_message_id(message, payload, live_message),
            delivery_key=_build_delivery_key(update_type, payload, live_message),
            payload=InboundMessage(
                content_type=content_type,
                text=text,
                caption=caption,
                attachments=attachments,
                metadata={
                    "raw_message": message,
                    "marker": payload.get("marker"),
                    "recipient_user_id": recipient.get("user_id") or recipient.get("userId"),
                    "chat_type": recipient.get("chat_type") or recipient.get("chatType"),
                    "user_locale": payload.get("user_locale"),
                },
            ),
            raw=payload,
        )

    if update_type == "message_callback":
        callback = payload.get("callback", {})
        return InboundEventEnvelope(
            event_type=InboundEventType.CALLBACK,
            vendor_event_name=update_type,
            chat_id=str(callback.get("chat_id") or payload.get("chat_id") or "") or None,
            user_id=str(callback.get("user", {}).get("user_id") or payload.get("user_id") or "") or None,
            message_id=str(callback.get("message", {}).get("mid") or "") or None,
            delivery_key=_build_delivery_key(update_type, payload, live_message),
            payload=InboundCallback(
                callback_id=callback.get("id"),
                data=callback.get("payload"),
                origin_message_id=callback.get("message", {}).get("mid"),
                origin_chat_id=str(callback.get("chat_id") or "") or None,
                origin_user_id=str(callback.get("user", {}).get("user_id") or "") or None,
                metadata={"raw_callback": callback},
            ),
            raw=payload,
        )

    if update_type == "bot_started":
        return InboundEventEnvelope(
            event_type=InboundEventType.SERVICE,
            vendor_event_name=update_type,
            chat_id=str(payload.get("chat_id", "") or "") or None,
            user_id=str(payload.get("user_id", "") or "") or None,
            delivery_key=_build_delivery_key(update_type, payload, live_message),
            payload=InboundServiceEvent(service_type=update_type),
            raw=payload,
        )

    return InboundEventEnvelope.unsupported(
        vendor_event_name=update_type,
        chat_id=str(payload.get("chat_id", "") or "") or None,
        user_id=str(payload.get("user_id", "") or "") or None,
        delivery_key=_build_delivery_key(update_type, payload, live_message),
        raw=payload,
    )
