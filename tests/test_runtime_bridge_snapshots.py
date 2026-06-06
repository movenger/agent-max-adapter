from hermes_max_adapter.goclaw import build_goclaw_runtime_snapshot
from hermes_max_adapter.openclaw import build_openclaw_runtime_snapshot


class _OpenClawCfg:
    def __init__(self, *, bot_token="token", extra=None):
        self.bot_token = bot_token
        self.extra = extra or {
            "webhook_secret": "secret",
            "webhook_url": "https://example.com/webhook",
            "enable_long_polling": True,
            "max_retries": 3,
            "retry_backoff_seconds": 0.5,
            "request_timeout_seconds": 20,
            "redis_url": "redis://localhost:6379/0",
            "dedupe_ttl_seconds": 90,
        }


class _GoClawCfg:
    token = "token"
    webhook_secret = "secret"
    webhook_url = "https://example.com/webhook"
    enable_long_polling = False
    max_retries = 2
    retry_backoff_seconds = 0.25
    request_timeout_seconds = 15
    redis_url = "redis://localhost:6379/1"
    dedupe_ttl_seconds = 120


def test_openclaw_runtime_snapshot_normalizes_transport_fields():
    snapshot = build_openclaw_runtime_snapshot(_OpenClawCfg())

    assert snapshot == {
        "token": "token",
        "api_base": "https://botapi.max.ru",
        "webhook_url": "https://example.com/webhook",
        "webhook_secret": "secret",
        "enable_long_polling": True,
        "max_retries": 3,
        "retry_backoff_seconds": 0.5,
        "request_timeout_seconds": 20,
        "redis_url": "redis://localhost:6379/0",
        "dedupe_ttl_seconds": 90,
    }


def test_openclaw_runtime_snapshot_falls_back_to_extra_token_and_fails_closed():
    snapshot = build_openclaw_runtime_snapshot(
        _OpenClawCfg(bot_token="", extra={"token": "fallback-token", "webhook_secret": "secret"})
    )
    assert snapshot["token"] == "fallback-token"

    try:
        build_openclaw_runtime_snapshot(_OpenClawCfg(bot_token="", extra={"webhook_secret": "secret"}))
    except ValueError as exc:
        assert str(exc) == "MAX OpenClaw config missing required token"
    else:
        raise AssertionError("expected ValueError for missing token")


def test_goclaw_runtime_snapshot_normalizes_transport_fields():
    snapshot = build_goclaw_runtime_snapshot(_GoClawCfg())

    assert snapshot == {
        "token": "token",
        "api_base": "https://botapi.max.ru",
        "webhook_url": "https://example.com/webhook",
        "webhook_secret": "secret",
        "enable_long_polling": False,
        "max_retries": 2,
        "retry_backoff_seconds": 0.25,
        "request_timeout_seconds": 15,
        "redis_url": "redis://localhost:6379/1",
        "dedupe_ttl_seconds": 120,
    }


def test_goclaw_runtime_snapshot_requires_token():
    class _MissingTokenCfg:
        token = ""
        webhook_secret = "secret"
        webhook_url = None
        enable_long_polling = False
        max_retries = 2
        retry_backoff_seconds = 0.0
        request_timeout_seconds = 15
        redis_url = None
        dedupe_ttl_seconds = 3600

    try:
        build_goclaw_runtime_snapshot(_MissingTokenCfg())
    except ValueError as exc:
        assert str(exc) == "MAX GoClaw config missing required token"
    else:
        raise AssertionError("expected ValueError for missing token")
