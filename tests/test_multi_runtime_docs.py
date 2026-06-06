from pathlib import Path


def test_multi_runtime_integration_doc_mentions_attach_ready_boundary_and_next_steps():
    content = Path("docs/integration/multi-runtime.md").read_text().lower()
    assert "openclaw attach-ready surface" in content
    assert "goclaw attach-ready surface" in content
    assert "not yet proven live" in content
    assert "real upstream runtime" in content


def test_openclaw_attach_guide_exists_and_mentions_plugin_factory_and_webhook_checks():
    content = Path("docs/integration/openclaw-attach.md").read_text().lower()
    assert "plugin_factory" in content
    assert "validate_webhook_request" in content
    assert "ingest_webhook" in content
    assert "status()" in content


def test_goclaw_attach_guide_exists_and_mentions_channel_factory_and_receive_flow():
    content = Path("docs/integration/goclaw-attach.md").read_text().lower()
    assert "create_goclaw_channel" in content
    assert "receive()" in content
    assert "push_update" in content
    assert "status()" in content
