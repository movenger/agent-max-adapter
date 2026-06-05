from pathlib import Path


def test_readme_mentions_token_only_mode():
    content = Path("README.md").read_text()
    assert "token-only" in content.lower()
    assert "live outbound smoke" in content.lower()
