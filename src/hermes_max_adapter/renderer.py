from __future__ import annotations

import re

from hermes_max_adapter.models.actions import ActionButtonKind
from hermes_max_adapter.models.attachments import AttachmentKind
from hermes_max_adapter.models.max_messages import (
    OutboundActionRowPart,
    OutboundAttachmentPart,
    OutboundMessage,
    OutboundTextPart,
)
from hermes_max_adapter.upload import build_outbound_attachment_payload

_UNSUPPORTED_FORMATTING_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\|\|(.+?)\|\|", r"\1"),
)


def downgrade_formatting(text: str) -> str:
    downgraded = text
    for pattern, replacement in _UNSUPPORTED_FORMATTING_PATTERNS:
        downgraded = re.sub(pattern, replacement, downgraded)
    return downgraded


def chunk_text(text: str, limit: int) -> list[str]:
    if limit <= 0 or len(text) <= limit:
        return [text]
    return [text[i:i + limit] for i in range(0, len(text), limit)]


def _merge_attachment_payload(payload: dict, attachment_payload: dict) -> None:
    for key, value in attachment_payload.items():
        if key == "attachments":
            payload.setdefault("attachments", [])
            payload["attachments"].extend(value)
            continue
        payload[key] = value


def _render_action_rows(part: OutboundActionRowPart) -> dict:
    return {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {
                        "type": str(button.kind),
                        "text": button.text,
                        **({"payload": button.payload} if button.payload is not None else {}),
                        **({"url": button.url} if button.url is not None else {}),
                    }
                    for button in row
                ]
                for row in part.rows
            ]
        },
    }


def _render_attachment(part: OutboundAttachmentPart) -> dict:
    attachment = part.attachment
    payload = build_outbound_attachment_payload(attachment)
    if attachment.remote_id is not None:
        payload["id"] = attachment.remote_id
    return payload


def render_canonical_outbound_message(message: OutboundMessage, limit: int = 4000) -> list[dict]:
    text_parts = [part for part in message.parts if isinstance(part, OutboundTextPart)]
    attachment_parts = [part for part in message.parts if isinstance(part, OutboundAttachmentPart)]
    action_parts = [part for part in message.parts if isinstance(part, OutboundActionRowPart)]

    payload: dict = {}
    if text_parts:
        combined_text = "\n".join(downgrade_formatting(part.text) for part in text_parts)
        chunks = chunk_text(combined_text, limit=limit)
        if len(chunks) > 1 and not attachment_parts and not action_parts:
            return [{"text": chunk} for chunk in chunks]
        payload["text"] = chunks[0]

    if attachment_parts:
        for part in attachment_parts:
            _merge_attachment_payload(payload, _render_attachment(part))
        if "text" not in payload:
            first_caption = next((part.caption for part in attachment_parts if part.caption), None)
            if first_caption is not None:
                payload["text"] = downgrade_formatting(first_caption)

    if action_parts:
        payload.setdefault("attachments", [])
        payload["attachments"].extend(_render_action_rows(part) for part in action_parts)

    return [payload]


def render_outbound_payload(text: str, limit: int = 4000) -> list[dict[str, str]]:
    message = OutboundMessage(parts=[OutboundTextPart(text=text)])
    return render_canonical_outbound_message(message, limit=limit)
