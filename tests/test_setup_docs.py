from pathlib import Path


def test_readme_mentions_setup_wizard():
    content = Path("README.md").read_text()
    assert "scripts/setup.py" in content
    assert "wizard" in content.lower()


def test_readme_mentions_dependency_checks_and_guided_install():
    content = Path("README.md").read_text().lower()
    assert "docker compose" in content
    assert "dependency" in content or "dependencies" in content
    assert "install" in content
    assert "smoke" in content
