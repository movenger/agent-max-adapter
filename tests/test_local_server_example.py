from pathlib import Path


def test_local_server_example_exists():
    example = Path("examples/local_webhook_server.py")
    assert example.exists()
