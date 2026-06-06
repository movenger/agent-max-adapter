from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from queue import Empty, Queue
from typing import Any

from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.models.attachments import AttachmentKind
from hermes_max_adapter.updates import normalize_update


@dataclass(slots=True)
class GoClawMediaAttachment:
    type: str
    file_id: str
    file_name: str = ""
    mime_type: str = ""
    caption: str = ""
    data: bytes = b""


@dataclass(slots=True)
class GoClawInboundMessage:
    channel: str
    account_id: str
    chat_type: str
    sender_id: str
    sender_name: str
    text: str
    reply_to: str = ""
    media: list[GoClawMediaAttachment] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class GoClawOutboundMessage:
    chat_id: str
    text: str
    parse_mode: str = ""
    reply_markup: object | None = None


class GoClawMaxChannel:
    def __init__(self, adapter: MaxAdapter) -> None:
        self.name = "max"
        self.adapter = adapter
        self._status = "disconnected"
        self._inbound: Queue[GoClawInboundMessage] = Queue()
        self._last_event: dict | None = None

    def Name(self) -> str:
        return self.name

    def connect_sync(self) -> None:
        self.adapter.connect_sync()
        self._status = "connected"

    def Connect(self) -> None:
        self.connect_sync()

    def disconnect_sync(self) -> None:
        self.adapter.disconnect_sync()
        self._status = "disconnected"

    def Disconnect(self) -> None:
        self.disconnect_sync()

    def status(self) -> str:
        return self._status

    def snapshot(self) -> dict:
        return {
            "name": self.name,
            "status": self._status,
            "connected": self._status == "connected",
            "pending_inbound": self._inbound.qsize(),
            "last_event": self._last_event,
        }

    def runtime_snapshot(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        return {
            **snapshot,
            "attach_ready": True,
            "supports": {
                "outbound_send": True,
                "inbound_queue": True,
                "lifecycle": True,
                "normalized_updates": True,
            },
            "methods": [
                "Name",
                "Connect",
                "Disconnect",
                "Status",
                "Send",
                "Receive",
                "push_update",
                "receive_nowait",
                "runtime_snapshot",
                "attach_checklist",
            ],
        }

    def attach_checklist(self) -> list[str]:
        return [
            "Create channel with create_goclaw_channel(...) in GoClaw runtime",
            "Connect channel and confirm Status() == connected",
            "Send outbound message through Send(...) or send_sync(...)",
            "Inject normalized inbound update through push_update(...)",
            "Receive inbound message through Receive() or receive_nowait()",
        ]

    def Status(self) -> str:
        return self.status()

    def send_sync(self, msg: GoClawOutboundMessage) -> dict:
        return self.adapter.send_text_sync(chat_id=msg.chat_id, text=msg.text)

    def Send(self, msg: GoClawOutboundMessage) -> dict:
        return self.send_sync(msg)

    def push_update(self, payload: dict, received_at: datetime | None = None) -> None:
        event = normalize_update(payload)
        self._last_event = {
            "event_type": event.event_type,
            "vendor_event_name": event.vendor_event_name,
            "chat_id": event.chat_id,
            "user_id": event.user_id,
            "message_id": event.message_id,
        }
        if event.event_type != "message":
            return
        received_at = received_at or datetime.now(timezone.utc)
        media: list[GoClawMediaAttachment] = []
        for attachment in event.payload.attachments:
            media.append(
                GoClawMediaAttachment(
                    type=_map_attachment_kind(attachment.kind),
                    file_id=attachment.upload_token or "",
                    file_name=attachment.file_name or "",
                )
            )
        self._inbound.put(
            GoClawInboundMessage(
                channel="max",
                account_id=event.chat_id or "",
                chat_type=(event.payload.metadata or {}).get("chat_type") or "direct",
                sender_id=event.user_id or "",
                sender_name="",
                text=event.payload.text or event.payload.caption or "",
                media=media,
                timestamp=received_at,
            )
        )

    def receive_nowait(self) -> GoClawInboundMessage:
        try:
            return self._inbound.get_nowait()
        except Empty as exc:
            raise RuntimeError("no inbound message available") from exc

    def Receive(self) -> Queue[GoClawInboundMessage]:
        return self._inbound


def _map_attachment_kind(kind: AttachmentKind) -> str:
    mapping = {
        AttachmentKind.PHOTO: "photo",
        AttachmentKind.DOCUMENT: "document",
        AttachmentKind.AUDIO: "audio",
        AttachmentKind.VIDEO: "video",
        AttachmentKind.VOICE: "voice",
        AttachmentKind.STICKER: "sticker",
        AttachmentKind.ANIMATION: "animation",
        AttachmentKind.CONTACT: "contact",
        AttachmentKind.LOCATION: "location",
    }
    return mapping.get(kind, "unknown")


def _build_config(channel_config: object) -> MaxAdapterConfig:
    snapshot = build_goclaw_runtime_snapshot(channel_config)
    return MaxAdapterConfig(
        bot_token=snapshot["token"],
        webhook_secret=snapshot["webhook_secret"],
        webhook_url=snapshot["webhook_url"],
        enable_long_polling=snapshot["enable_long_polling"],
        max_retries=snapshot["max_retries"],
        retry_backoff_seconds=snapshot["retry_backoff_seconds"],
        request_timeout_seconds=snapshot["request_timeout_seconds"],
        redis_url=snapshot["redis_url"],
        dedupe_ttl_seconds=snapshot["dedupe_ttl_seconds"],
    )


def build_goclaw_runtime_snapshot(channel_config: object) -> dict[str, Any]:
    token = str(getattr(channel_config, "token", "") or "").strip()
    if not token:
        raise ValueError("MAX GoClaw config missing required token")
    return {
        "token": token,
        "api_base": str(getattr(channel_config, "api_base", "") or "https://botapi.max.ru"),
        "webhook_url": getattr(channel_config, "webhook_url", None),
        "webhook_secret": str(getattr(channel_config, "webhook_secret", "") or ""),
        "enable_long_polling": bool(getattr(channel_config, "enable_long_polling", False)),
        "max_retries": int(getattr(channel_config, "max_retries", 2)),
        "retry_backoff_seconds": float(getattr(channel_config, "retry_backoff_seconds", 0.0)),
        "request_timeout_seconds": int(getattr(channel_config, "request_timeout_seconds", 15)),
        "redis_url": getattr(channel_config, "redis_url", None),
        "dedupe_ttl_seconds": int(getattr(channel_config, "dedupe_ttl_seconds", 3600)),
    }


def create_goclaw_channel(channel_config: object, sender: object | None = None) -> GoClawMaxChannel:
    adapter = MaxAdapter(config=_build_config(channel_config), sender=sender)
    return GoClawMaxChannel(adapter=adapter)
