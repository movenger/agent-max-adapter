from pathlib import Path


def test_watchdog_script_exists():
    assert Path("scripts/watchdog.py").exists()
