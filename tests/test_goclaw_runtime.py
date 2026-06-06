from hermes_max_adapter.adapter import MaxAdapter


class _FakeChannelConfig:
    def __init__(self):
        self.token = "token"
        self.webhook_secret = "secret"
        self.webhook_url = "https://example.com/webhook"
        self.enable_long_polling = True
        self.max_retries = 3
        self.retry_backoff_seconds = 0.5
        self.request_timeout_seconds = 20


def test_goclaw_channel_factory_builds_max_adapter_backed_channel():
    from hermes_max_adapter.goclaw import create_goclaw_channel

    channel = create_goclaw_channel(_FakeChannelConfig())

    assert channel.name == "max"
    assert isinstance(channel.adapter, MaxAdapter)
    assert channel.adapter.config.bot_token == "token"
    assert channel.snapshot()["status"] == "disconnected"
