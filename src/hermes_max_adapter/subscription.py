from __future__ import annotations

from hermes_max_adapter.config import MaxAdapterConfig


def build_subscribe_request(config: MaxAdapterConfig) -> dict:
    return {
        "method": "POST",
        "url": "https://platform-api.max.ru/subscriptions",
        "headers": {
            "Authorization": config.bot_token,
            "Content-Type": "application/json",
        },
        "json": {
            "url": config.webhook_url,
            "secret": config.webhook_secret,
        },
    }


def build_subscription_reconcile_plan(config: MaxAdapterConfig, current: list[dict]) -> dict:
    for item in current:
        if item.get("url") == config.webhook_url and item.get("secret") == config.webhook_secret:
            return {"action": "keep", "reason": "matching_subscription_present"}
    return {
        "action": "resubscribe",
        "reason": "subscription_missing_or_mismatched",
        "request": build_subscribe_request(config),
    }


def apply_subscription_reconcile_plan(plan: dict, sender: object) -> dict:
    if plan.get("action") == "keep":
        return {"applied": False, "reason": plan.get("reason")}
    request = plan["request"]
    response = sender.send(request)
    return {
        "applied": True,
        "reason": plan.get("reason"),
        "response": response,
    }
