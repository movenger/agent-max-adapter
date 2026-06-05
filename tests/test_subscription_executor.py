from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.subscription import (
    apply_subscription_reconcile_plan,
    build_subscription_reconcile_plan,
)


class StubSubscriptionSender:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send(self, request: dict) -> dict:
        self.calls.append(request)
        return {"status_code": 200}


def test_apply_reconcile_plan_executes_resubscribe_request():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://bot.example.com/webhook",
        enable_long_polling=False,
    )
    current = [{"url": "https://old.example.com/webhook", "secret": "secret"}]
    plan = build_subscription_reconcile_plan(config, current)
    sender = StubSubscriptionSender()

    result = apply_subscription_reconcile_plan(plan, sender)

    assert result["applied"] is True
    assert len(sender.calls) == 1
    assert sender.calls[0]["url"].endswith("/subscriptions")
