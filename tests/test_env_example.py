from pathlib import Path


def test_env_example_exists_and_mentions_redis_url():
    content = Path(".env.example").read_text()
    assert "REDIS_URL=" in content
    assert "MAX_BOT_TOKEN=" in content
