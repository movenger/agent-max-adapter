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


def test_live_smoke_script_exists():
    assert Path("scripts/live_smoke.py").exists()


def test_live_smoke_script_reports_ready_when_bot_token_and_webhook_url_present(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MAX_BOT_TOKEN", "token")
    monkeypatch.setenv("MAX_WEBHOOK_URL", "https://example.com/webhook")
    monkeypatch.setenv("MAX_WEBHOOK_SECRET", "secret")

    module = _load_script_module("live_smoke_script", "scripts/live_smoke.py")

    module.main()
    output = capsys.readouterr().out
    assert "LIVE_SMOKE_READY" in output
    assert "CALLBACK_PREVIEW" in output


def test_live_smoke_script_mentions_callback_preview_contract():
    content = Path("scripts/live_smoke.py").read_text()
    assert "build_answer_callback_request" in content
    assert "CALLBACK_PREVIEW" in content
