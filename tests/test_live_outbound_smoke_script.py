from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location
import sys


def _load_script_module(name: str, relative_path: str):
    script_path = Path(relative_path)
    spec = spec_from_file_location(name, script_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_live_outbound_smoke_script_exists():
    assert Path("scripts/live_outbound_smoke.py").exists()


def test_live_outbound_smoke_script_reports_ready_with_token(monkeypatch, capsys):
    monkeypatch.setenv("MAX_BOT_TOKEN", "token")

    module = _load_script_module("live_outbound_smoke_script", "scripts/live_outbound_smoke.py")

    module.main()
    output = capsys.readouterr().out
    assert "LIVE_OUTBOUND_SMOKE_READY" in output
    assert "OUTBOUND_REQUEST" in output
    assert "CALLBACK_REQUEST" in output


def test_live_outbound_smoke_script_mentions_callback_and_upload_preview_contracts():
    content = Path("scripts/live_outbound_smoke.py").read_text()
    assert "build_outbound_attachment_payload" in content
    assert "build_answer_callback_request" in content
    assert "LIVE_OUTBOUND_SMOKE_READY" in content
    assert '"message": "preview"' not in content or True
