from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.webhook_app import WebhookApplication
from hermes_max_adapter.webhook_server import validate_secret


@dataclass(slots=True)
class OpenClawRuntimeConfig:
    bot_token: str = ""
    extra: dict[str, Any] | None = None


class _RuntimeAdapter(Protocol):
    def connect_sync(self) -> bool: ...
    def disconnect_sync(self) -> None: ...
    def status(self) -> dict[str, Any]: ...
    def process_update(self, payload: dict) -> dict: ...


class OpenClawMaxPlugin:
    def __init__(self, adapter: _RuntimeAdapter, webhook_secret: str) -> None:
        self.runtime_id = "max"
        self.label = "MAX"
        self.adapter = adapter
        self.webhook_secret = webhook_secret
        self._webhook_app = WebhookApplication(adapter=adapter, webhook_secret=webhook_secret)

    def start(self) -> None:
        self.adapter.connect_sync()

    def stop(self) -> None:
        self.adapter.disconnect_sync()

    def status(self) -> dict[str, Any]:
        adapter_status = self.adapter.status()
        return {
            "runtime_id": self.runtime_id,
            "label": self.label,
            "connected": bool(adapter_status.get("connected", False)),
            "webhook_enabled": bool(adapter_status.get("config", {}).get("webhook_enabled", False)),
            "long_polling_enabled": bool(adapter_status.get("config", {}).get("long_polling_enabled", False)),
        }

    def runtime_snapshot(self) -> dict[str, Any]:
        status = self.status()
        return {
            **status,
            "attach_ready": True,
            "supports": {
                "webhook_ingress": True,
                "long_polling": True,
                "outbound_send": True,
                "inbound_process_update": True,
            },
            "methods": [
                "start",
                "stop",
                "status",
                "runtime_snapshot",
                "attach_checklist",
                "validate_webhook_request",
                "ingest_webhook",
                "process_update",
            ],
        }

    def attach_checklist(self) -> list[str]:
        return [
            "Load registration and validate config in OpenClaw runtime",
            "Start plugin and confirm connected status()",
            "Validate webhook secret handling with validate_webhook_request(...)",
            "Post a webhook body through ingest_webhook(...) and confirm process_update(...) runs",
            "Run outbound send through underlying MAX adapter core",
        ]

    def validate_webhook_request(self, headers: dict[str, str]) -> bool:
        return validate_secret(self.webhook_secret, headers.get("X-Max-Bot-Api-Secret"))

    def ingest_webhook(self, headers: dict[str, str], body: bytes) -> tuple[int, bytes]:
        return self._webhook_app.handle_request(headers=headers, body=body)

    def process_update(self, payload: dict) -> dict:
        return self.adapter.process_update(payload)


def _runtime_extra(config: object) -> dict[str, Any]:
    extra = getattr(config, "extra", {}) or {}
    return extra if isinstance(extra, dict) else {}


def build_openclaw_runtime_snapshot(config: object) -> dict[str, Any]:
    extra = _runtime_extra(config)
    token = (getattr(config, "bot_token", "") or extra.get("token", "")).strip()
    if not token:
        raise ValueError("MAX OpenClaw config missing required token")
    return {
        "token": token,
        "api_base": str(extra.get("api_base") or "https://botapi.max.ru"),
        "webhook_url": extra.get("webhook_url"),
        "webhook_secret": str(extra.get("webhook_secret") or ""),
        "enable_long_polling": bool(extra.get("enable_long_polling", False)),
        "max_retries": int(extra.get("max_retries", 2)),
        "retry_backoff_seconds": float(extra.get("retry_backoff_seconds", 0.0)),
        "request_timeout_seconds": int(extra.get("request_timeout_seconds", 15)),
        "redis_url": extra.get("redis_url"),
        "dedupe_ttl_seconds": int(extra.get("dedupe_ttl_seconds", 3600)),
    }


def _build_config_from_runtime_config(config: object) -> MaxAdapterConfig:
    snapshot = build_openclaw_runtime_snapshot(config)
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


def validate_openclaw_config(config: object) -> bool:
    try:
        build_openclaw_runtime_snapshot(config)
    except ValueError:
        return False
    return True


def build_openclaw_manifest() -> dict[str, Any]:
    return {
        "runtime_id": "max",
        "label": "MAX",
        "entrypoint": "hermes_max_adapter.openclaw:build_openclaw_registration",
        "capabilities": {
            "ingress": ["webhook"],
            "egress": ["text", "document", "image", "video"],
            "runtime_mode": ["webhook", "long_polling"],
        },
    }


def build_openclaw_registration() -> dict:
    return {
        "runtime_id": "max",
        "label": "MAX",
        "manifest": build_openclaw_manifest(),
        "validate_config": validate_openclaw_config,
        "config_factory": _build_config_from_runtime_config,
        "plugin_factory": lambda cfg: OpenClawMaxPlugin(
            adapter=MaxAdapter(config=_build_config_from_runtime_config(cfg)),
            webhook_secret=_build_config_from_runtime_config(cfg).webhook_secret,
        ),
        "adapter_factory": lambda cfg: MaxAdapter(config=_build_config_from_runtime_config(cfg)),
        "supports_webhook_ingress": True,
        "supports_long_polling": True,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
