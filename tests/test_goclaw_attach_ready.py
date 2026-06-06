from hermes_max_adapter.goclaw import GoClawOutboundMessage, create_goclaw_channel


class _Cfg:
    token = "token"
    webhook_secret = "secret"
    webhook_url = "https://example.com/webhook"
    enable_long_polling = False
    max_retries = 2
    retry_backoff_seconds = 0.0
    request_timeout_seconds = 15


class _Sender:
    def send(self, request):
        return {"status_code": 200, "body": {"message_id": "m-1"}}


def test_goclaw_channel_exposes_attach_ready_snapshot_and_checklist():
    channel = create_goclaw_channel(_Cfg(), sender=_Sender())
    channel.connect_sync()

    snapshot = channel.runtime_snapshot()
    checklist = channel.attach_checklist()

    assert snapshot["name"] == "max"
    assert snapshot["attach_ready"] is True
    assert snapshot["supports"]["outbound_send"] is True
    assert snapshot["supports"]["inbound_queue"] is True
    assert "push_update" in snapshot["methods"]
    assert "receive_nowait" in snapshot["methods"]
    assert any("create channel" in item.lower() for item in checklist)
    assert any("connect" in item.lower() for item in checklist)
    assert any("send outbound" in item.lower() for item in checklist)
    assert any("receive inbound" in item.lower() for item in checklist)


def test_goclaw_channel_push_update_tracks_target_resolution_state():
    channel = create_goclaw_channel(_Cfg(), sender=_Sender())
    channel.connect_sync()

    payload = {
        "update_type": "message_created",
        "message": {
            "body": {"mid": "mid-1", "text": "incoming"},
            "recipient": {"chat_id": "12345", "chat_type": "direct"},
            "sender": {"user_id": "67890"},
        },
    }
    channel.push_update(payload)

    snapshot = channel.runtime_snapshot()
    assert snapshot["pending_inbound"] == 1
    assert snapshot["last_event"]["chat_id"] == "12345"
    assert snapshot["last_event"]["user_id"] == "67890"

    result = channel.send_sync(GoClawOutboundMessage(chat_id="12345", text="hello"))
    assert result["success"] is True
