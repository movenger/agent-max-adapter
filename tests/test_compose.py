from pathlib import Path


def test_compose_file_exists_and_mentions_redis():
    content = Path("compose.yaml").read_text()
    assert "redis" in content.lower()
    assert "6379" in content
