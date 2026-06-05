from pathlib import Path


def test_deploy_doc_mentions_systemd_and_watchdog():
    content = Path("docs/specs/deployment.md").read_text()
    assert "systemd" in content.lower()
    assert "watchdog" in content.lower()
    assert "subscriptions" in content.lower()
