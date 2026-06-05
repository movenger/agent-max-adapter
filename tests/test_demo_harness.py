from pathlib import Path


def test_demo_harness_file_exists():
    demo = Path("examples/local_demo.py")
    assert demo.exists()
