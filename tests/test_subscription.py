from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.subscription import build_subscribe_request, build_subscription_reconcile_plan


def test_build_subscribe_request_uses_configured_url_and_secret():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://bot.example.com/webhook",
        enable_long_polling=False,
    )
    request = build_subscribe_request(config)
    assert request["method"] == "POST"
    assert request["url"].endswith("/subscriptions")
    assert request["json"]["url"] == "https://bot.example.com/webhook"
    assert request["json"]["secret"] == "secret"


def test_reconcile_plan_requests_resubscribe_when_url_mismatches():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://bot.example.com/webhook",
        enable_long_polling=False,
    )
    current = [{"url": "https://old.example.com/webhook", "secret": "secret"}]
    plan = build_subscription_reconcile_plan(config, current)
    assert plan["action"] == "resubscribe"


def test_reconcile_plan_keeps_subscription_when_matching():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://bot.example.com/webhook",
        enable_long_polling=False,
    )
    current = [{"url": "https://bot.example.com/webhook", "secret": "secret"}]
    plan = build_subscription_reconcile_plan(config, current)
    assert plan["action"] == "keep"
