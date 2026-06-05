from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AttachmentKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    STICKER = "sticker"
    ANIMATION = "animation"
    CONTACT = "contact"
    LOCATION = "location"
    UNKNOWN = "unknown"


class AttachmentSourceKind(StrEnum):
    VENDOR_PAYLOAD = "vendor_payload"
    VENDOR_TOKEN = "vendor_token"
    EXTERNAL_URL = "external_url"
    LOCAL_FILE = "local_file"
    IN_MEMORY = "in_memory"
    GENERATED = "generated"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class AttachmentRef:
    kind: AttachmentKind
    source: AttachmentSourceKind
    remote_id: str | None = None
    upload_token: str | None = None
    url: str | None = None
    local_path: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    duration_seconds: int | None = None
    width: int | None = None
    height: int | None = None
    thumbnail: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
