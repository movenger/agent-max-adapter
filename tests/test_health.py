from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig


def test_adapter_health_reports_connection_and_metrics():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    adapter = MaxAdapter(config=config)
    adapter.connect_sync()
    adapter.process_update(
        {
            "update_type": "message_created",
            "chat_id": "c1",
            "user_id": "u1",
            "message": {"body": {"text": "hello"}},
            "mid": "m1",
        }
    )

    health = adapter.health_status()

    assert health["connected"] is True
    assert health["metrics"]["inbound_updates_total"] == 1
    assert health["config"]["webhook_enabled"] is True
