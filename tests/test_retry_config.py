from hermes_max_adapter.config import MaxAdapterConfig


def test_config_reads_retry_policy(monkeypatch):
    monkeypatch.setenv("MAX_BOT_TOKEN", "token")
    monkeypatch.setenv("MAX_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("MAX_MAX_RETRIES", "4")
    monkeypatch.setenv("MAX_RETRY_BACKOFF_SECONDS", "1.5")

    cfg = MaxAdapterConfig.from_env()

    assert cfg.max_retries == 4
    assert cfg.retry_backoff_seconds == 1.5
