from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class SupportLevel(StrEnum):
    FULL = "full"
    DEGRADED = "degraded"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
