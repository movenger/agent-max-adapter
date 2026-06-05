from pathlib import Path


def test_readme_mentions_compose_and_redis_smoke():
    content = Path("README.md").read_text()
    assert "docker compose" in content.lower()
    assert "redis_smoke" in content
