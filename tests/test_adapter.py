from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig


def test_adapter_connect_marks_adapter_ready():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    adapter = MaxAdapter(config=config)
    assert adapter.connected is False
    assert adapter.connect_sync() is True
    assert adapter.connected is True


def test_adapter_disconnect_marks_adapter_not_ready():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    adapter = MaxAdapter(config=config)
    adapter.connect_sync()
    adapter.disconnect_sync()
    assert adapter.connected is False
