from hermes_max_adapter.adapter import MaxAdapter


class _Cfg:
    def __init__(self):
        self.bot_token = "token"
        self.extra = {
            "token": "token",
            "webhook_secret": "secret",
            "webhook_url": "https://example.com/webhook",
            "enable_long_polling": True,
            "max_retries": 3,
            "retry_backoff_seconds": 0.5,
            "request_timeout_seconds": 20,
        }


class _Sender:
    def __init__(self):
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        return {"status_code": 200, "body": {"message_id": "m-1"}}


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
                "long_polling_enabled": False,
            },
        }

    def process_update(self, payload):
        self.processed.append(payload)
        return {"event": "ok", "payload": payload}


def test_openclaw_registration_exposes_factory_and_validate_config():
    from hermes_max_adapter.openclaw import build_openclaw_registration

    registration = build_openclaw_registration()

    assert registration["runtime_id"] == "max"
    assert callable(registration["validate_config"])
    assert callable(registration["adapter_factory"])
    assert callable(registration["plugin_factory"])
    assert registration["validate_config"](_Cfg()) is True

    adapter = registration["adapter_factory"](_Cfg())
    assert isinstance(adapter, MaxAdapter)


def test_openclaw_registration_exposes_manifest_and_plugin_runtime_shape():
    from hermes_max_adapter.openclaw import OpenClawMaxPlugin, build_openclaw_manifest, build_openclaw_registration

    manifest = build_openclaw_manifest()
    assert manifest["runtime_id"] == "max"
    assert manifest["capabilities"]["ingress"] == ["webhook"]
    assert "video" in manifest["capabilities"]["egress"]

    registration = build_openclaw_registration()
    plugin = registration["plugin_factory"](_Cfg())
    assert isinstance(plugin, OpenClawMaxPlugin)

    plugin.start()
    status = plugin.status()
    assert status["runtime_id"] == "max"
    assert status["connected"] is True
    assert status["webhook_enabled"] is True
    plugin.stop()
    assert plugin.status()["connected"] is False


def test_openclaw_plugin_ingests_webhook_and_validates_secret():
    from hermes_max_adapter.openclaw import OpenClawMaxPlugin

    adapter = _AdapterStub()
    plugin = OpenClawMaxPlugin(adapter=adapter, webhook_secret="secret")

    assert plugin.validate_webhook_request({"X-Max-Bot-Api-Secret": "secret"}) is True
    assert plugin.validate_webhook_request({"X-Max-Bot-Api-Secret": "wrong"}) is False

    status_code, body = plugin.ingest_webhook(
        headers={"X-Max-Bot-Api-Secret": "secret"},
        body=b'{"update_type":"message_created","message":{"body":{"text":"hi"},"recipient":{"chat_id":"c-1"},"sender":{"user_id":"u-1"}}}',
    )
    assert status_code == 200
    assert body == b"ok"
    assert adapter.processed[0]["update_type"] == "message_created"
