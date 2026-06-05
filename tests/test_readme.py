from pathlib import Path


def test_readme_mentions_quickstart_and_demo():
    content = Path("README.md").read_text()
    assert "Quickstart" in content
    assert "examples/local_demo.py" in content
    assert "MAX_BOT_TOKEN" in content
