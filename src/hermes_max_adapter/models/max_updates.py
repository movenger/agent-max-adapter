from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from hermes_max_adapter.models.attachments import AttachmentRef


class InboundEventType(StrEnum):
    MESSAGE = "message"
    CALLBACK = "callback"
    SERVICE = "service"
    UNSUPPORTED = "unsupported"


class MessageContentType(StrEnum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    STICKER = "sticker"
    ANIMATION = "animation"
    CONTACT = "contact"
    LOCATION = "location"
    MEDIA_GROUP = "media_group"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class InboundMessage:
    content_type: MessageContentType
    text: str | None = None
    caption: str | None = None
    attachments: list[AttachmentRef] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    reply_to_message_id: str | None = None
    thread_id: str | None = None
    sender_display_name: str | None = None
    chat_title: str | None = None
    album_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InboundCallback:
    callback_id: str | None = None
    data: str | None = None
    button_text: str | None = None
    origin_message_id: str | None = None
    origin_chat_id: str | None = None
    origin_user_id: str | None = None
    notification_supported: bool | None = None
    edit_supported: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InboundServiceEvent:
    service_type: str
    summary: str | None = None
    actor_user_id: str | None = None
    target_user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class UnsupportedInboundPayload:
    reason: str = "unsupported"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InboundEventEnvelope:
    event_type: InboundEventType
    vendor_event_name: str
    delivery_key: str
    payload: InboundMessage | InboundCallback | InboundServiceEvent | UnsupportedInboundPayload
    chat_id: str | None = None
    user_id: str | None = None
    message_id: str | None = None
    event_id: str | None = None
    occurred_at: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    degradation_flags: list[str] = field(default_factory=list)

    @classmethod
    def message(
        cls,
        *,
        vendor_event_name: str,
        chat_id: str | None,
        user_id: str | None,
        message_id: str | None,
        delivery_key: str,
        payload: InboundMessage,
        raw: dict[str, Any] | None = None,
    ) -> "InboundEventEnvelope":
        return cls(
            event_type=InboundEventType.MESSAGE,
            vendor_event_name=vendor_event_name,
            chat_id=chat_id,
            user_id=user_id,
            message_id=message_id,
            delivery_key=delivery_key,
            payload=payload,
            raw=raw or {},
        )

    @classmethod
    def unsupported(
        cls,
        *,
        vendor_event_name: str,
        chat_id: str | None,
        user_id: str | None,
        delivery_key: str,
        raw: dict[str, Any] | None = None,
    ) -> "InboundEventEnvelope":
        return cls(
            event_type=InboundEventType.UNSUPPORTED,
            vendor_event_name=vendor_event_name,
            chat_id=chat_id,
            user_id=user_id,
            delivery_key=delivery_key,
            payload=UnsupportedInboundPayload(),
            raw=raw or {},
        )

    @property
    def kind(self) -> str:
        return str(self.event_type)

    @property
    def text(self) -> str | None:
        if isinstance(self.payload, InboundMessage):
            return self.payload.text
        return None

    @property
    def update_type(self) -> str:
        return self.vendor_event_name


NormalizedEvent = InboundEventEnvelope
