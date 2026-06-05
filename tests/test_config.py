from hermes_max_adapter.config import MaxAdapterConfig


def test_config_reads_required_env_values(monkeypatch):
    monkeypatch.setenv("MAX_BOT_TOKEN", "token")
    monkeypatch.setenv("MAX_WEBHOOK_SECRET", "secret")
    cfg = MaxAdapterConfig.from_env()
    assert cfg.bot_token == "token"
    assert cfg.webhook_secret == "secret"
    assert cfg.enable_long_polling is False
