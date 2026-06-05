from pathlib import Path


def test_redis_smoke_script_exists():
    assert Path("scripts/redis_smoke.py").exists()
