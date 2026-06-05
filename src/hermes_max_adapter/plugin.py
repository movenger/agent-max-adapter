from __future__ import annotations

from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig


def validate_config(config: object) -> bool:
    extra = getattr(config, "extra", {}) or {}
    return bool(
        getattr(config, "bot_token", None)
        or extra.get("token")
    )


def build_registration() -> dict:
    return {
        "name": "max",
        "label": "MAX",
        "required_env": ["MAX_BOT_TOKEN"],
        "cron_deliver_env_var": "MAX_HOME_CHANNEL",
        "max_message_length": 4000,
        "emoji": "💬",
        "validate_config": validate_config,
        "adapter_factory": lambda cfg: MaxAdapter(
            config=MaxAdapterConfig(
                bot_token=getattr(cfg, "bot_token", "") or ((getattr(cfg, "extra", {}) or {}).get("token", "")),
                webhook_secret=((getattr(cfg, "extra", {}) or {}).get("webhook_secret", "")),
                webhook_url=((getattr(cfg, "extra", {}) or {}).get("webhook_url")),
                enable_long_polling=bool((getattr(cfg, "extra", {}) or {}).get("enable_long_polling", False)),
            )
        ),
    }
