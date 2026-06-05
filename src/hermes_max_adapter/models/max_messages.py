from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hermes_max_adapter.models.actions import ActionButton
from hermes_max_adapter.models.attachments import AttachmentRef


@dataclass(slots=True)
class OutboundTextPart:
    text: str
    entities: list[dict[str, Any]] = field(default_factory=list)
    allow_chunking: bool = True


@dataclass(slots=True)
class OutboundAttachmentPart:
    attachment: AttachmentRef
    caption: str | None = None
    caption_entities: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class OutboundActionRowPart:
    rows: list[list[ActionButton]]


@dataclass(slots=True)
class OutboundMessage:
    target_chat_id: str | None = None
    target_user_id: str | None = None
    parts: list[OutboundTextPart | OutboundAttachmentPart | OutboundActionRowPart] = field(default_factory=list)
    reply_to_message_id: str | None = None
    thread_id: str | None = None
    formatting_mode: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
