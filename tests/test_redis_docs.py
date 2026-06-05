from pathlib import Path


def test_readme_mentions_real_redis_mode():
    content = Path("README.md").read_text()
    assert "redis" in content.lower()
    assert "dedupe" in content.lower()
    assert "REDIS_URL" in content
