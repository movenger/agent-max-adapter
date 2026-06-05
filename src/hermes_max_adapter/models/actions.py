from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ActionButtonKind(StrEnum):
    CALLBACK = "callback"
    LINK = "link"
    MESSAGE = "message"
    OPEN_APP = "open_app"
    CLIPBOARD = "clipboard"
    REQUEST_CONTACT = "request_contact"
    REQUEST_LOCATION = "request_location"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class ActionButton:
    kind: ActionButtonKind
    text: str
    payload: str | None = None
    url: str | None = None
    app_ref: str | None = None
    copy_text: str | None = None
    request_contact: bool = False
    request_location: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
