from datetime import datetime, timezone


class _Sender:
    def send(self, request):
        return {"status_code": 200, "body": {"message_id": "m-1"}}


def test_goclaw_channel_contract_maps_send_and_receive():
    from hermes_max_adapter.goclaw import GoClawOutboundMessage, create_goclaw_channel

    class _Cfg:
        token = "token"
        webhook_secret = "secret"
        webhook_url = None
        enable_long_polling = False
        max_retries = 2
        retry_backoff_seconds = 0.0
        request_timeout_seconds = 15

    channel = create_goclaw_channel(_Cfg(), sender=_Sender())

    channel.connect_sync()
    assert channel.Name() == "max"
    assert channel.status() == "connected"
    assert channel.Status() == "connected"
    assert channel.snapshot()["connected"] is True
    assert channel.snapshot()["pending_inbound"] == 0

    result = channel.send_sync(GoClawOutboundMessage(chat_id="12345", text="hello"))
    assert result["success"] is True

    payload = {
        "update_type": "message_created",
        "message": {
            "body": {"mid": "mid-1", "text": "incoming"},
            "recipient": {"chat_id": "chat-1", "chat_type": "direct"},
            "sender": {"user_id": "user-1"},
        },
    }
    channel.push_update(payload, received_at=datetime.now(timezone.utc))

    snap = channel.snapshot()
    assert snap["pending_inbound"] == 1
    assert snap["last_event"]["vendor_event_name"] == "message_created"

    inbound = channel.receive_nowait()
    assert channel.Receive() is not None
    assert inbound.channel == "max"
    assert inbound.account_id == "chat-1"
    assert inbound.sender_id == "user-1"
    assert inbound.text == "incoming"

    callback_payload = {
        "update_type": "message_callback",
        "callback": {
            "id": "cb-1",
            "chat_id": "chat-1",
            "user": {"user_id": "user-1"},
            "message": {"mid": "mid-1"},
        },
    }
    channel.push_update(callback_payload, received_at=datetime.now(timezone.utc))
    assert channel.snapshot()["last_event"]["vendor_event_name"] == "message_callback"

    channel.disconnect_sync()
    channel.Connect()
    assert channel.Status() == "connected"
    channel.Disconnect()
    assert channel.status() == "disconnected"
