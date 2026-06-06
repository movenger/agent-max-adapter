from hermes_max_adapter.openclaw import build_openclaw_registration


class _Cfg:
    def __init__(self):
        self.bot_token = "token"
        self.extra = {
            "token": "token",
            "webhook_secret": "secret",
            "webhook_url": "https://example.com/webhook",
            "enable_long_polling": True,
        }


class _AdapterStub:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.processed = []

    def connect_sync(self):
        self.started = True
        return True

    def disconnect_sync(self):
        self.stopped = True

    def status(self):
        return {
            "connected": self.started and not self.stopped,
            "config": {
                "webhook_enabled": True,
                "long_polling_enabled": True,
            },
        }

    def process_update(self, payload):
        self.processed.append(payload)
        return {"event": "ok", "payload": payload}


def test_openclaw_plugin_has_attach_ready_runtime_snapshot_and_capabilities():
    registration = build_openclaw_registration()
    plugin = registration["plugin_factory"](_Cfg())

    plugin.start()
    snapshot = plugin.runtime_snapshot()

    assert snapshot["runtime_id"] == "max"
    assert snapshot["attach_ready"] is True
    assert snapshot["supports"]["webhook_ingress"] is True
    assert snapshot["supports"]["long_polling"] is True
    assert "process_update" in snapshot["methods"]
    assert "ingest_webhook" in snapshot["methods"]


def test_openclaw_plugin_exposes_local_attach_checklist():
    registration = build_openclaw_registration()
    plugin = registration["plugin_factory"](_Cfg())

    checklist = plugin.attach_checklist()

    assert any("load registration" in item.lower() for item in checklist)
    assert any("start plugin" in item.lower() for item in checklist)
    assert any("webhook" in item.lower() for item in checklist)
    assert any("outbound" in item.lower() for item in checklist)


def test_openclaw_plugin_runtime_snapshot_works_with_custom_adapter_stub():
    from hermes_max_adapter.openclaw import OpenClawMaxPlugin

    plugin = OpenClawMaxPlugin(adapter=_AdapterStub(), webhook_secret="secret")
    plugin.start()
    snapshot = plugin.runtime_snapshot()

    assert snapshot["connected"] is True
    assert snapshot["webhook_enabled"] is True
    assert snapshot["long_polling_enabled"] is True
