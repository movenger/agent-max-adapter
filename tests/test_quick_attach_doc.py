from pathlib import Path


def test_quick_attach_doc_exists():
    assert Path("docs/integration/quick-attach.md").exists()


def test_quick_attach_doc_mentions_bootstrap_and_registration():
    content = Path("docs/integration/quick-attach.md").read_text().lower()
    assert "pip install -e . pytest" in content
    assert "build_registration" in content
