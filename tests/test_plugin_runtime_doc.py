from pathlib import Path


def test_plugin_runtime_doc_exists():
    assert Path("docs/specs/plugin-runtime.md").exists()
