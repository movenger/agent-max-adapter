from pathlib import Path


def test_readme_mentions_subscription_reconcile():
    content = Path("README.md").read_text()
    assert "subscription" in content.lower()
    assert "watchdog" in content.lower()
