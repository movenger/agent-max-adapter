from pathlib import Path


def test_readme_has_copy_paste_install_path():
    content = Path("README.md").read_text().lower()
    assert "pip install -e . pytest" in content
    assert "python scripts/setup.py" in content


def test_integration_doc_has_adapter_factory_example():
    content = Path("docs/integration/hermes.md").read_text().lower()
    assert "adapter_factory" in content
    assert "build_registration" in content
