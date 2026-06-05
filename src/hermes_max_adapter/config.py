from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class MaxAdapterConfig:
    bot_token: str
    webhook_secret: str
    webhook_url: str | None
    enable_long_polling: bool
    max_retries: int = 2
    retry_backoff_seconds: float = 0.0
    request_timeout_seconds: int = 15
    redis_url: str | None = None
    dedupe_ttl_seconds: int = 3600

    @classmethod
    def from_env(cls) -> "MaxAdapterConfig":
        return cls(
            bot_token=os.getenv("MAX_BOT_TOKEN", "").strip(),
            webhook_secret=os.getenv("MAX_WEBHOOK_SECRET", "").strip(),
            webhook_url=os.getenv("MAX_WEBHOOK_URL", "").strip() or None,
            enable_long_polling=os.getenv("MAX_ENABLE_LONG_POLLING", "false").lower() == "true",
            max_retries=int(os.getenv("MAX_MAX_RETRIES", "2")),
            retry_backoff_seconds=float(os.getenv("MAX_RETRY_BACKOFF_SECONDS", "0")),
            request_timeout_seconds=int(os.getenv("MAX_REQUEST_TIMEOUT_SECONDS", "15")),
            redis_url=os.getenv("REDIS_URL", "").strip() or None,
            dedupe_ttl_seconds=int(os.getenv("MAX_DEDUPE_TTL_SECONDS", "3600")),
        )
