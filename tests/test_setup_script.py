from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

setup_path = Path("scripts/setup.py")
spec = spec_from_file_location("setup_script", setup_path)
assert spec is not None and spec.loader is not None
setup_script = module_from_spec(spec)
sys.modules["setup_script"] = setup_script
spec.loader.exec_module(setup_script)
CommandResult = setup_script.CommandResult
EnvironmentStatus = setup_script.EnvironmentStatus


def test_setup_script_exists():
    assert Path("scripts/setup.py").exists()


def test_setup_script_mentions_auto_install_and_smoke_flow():
    content = Path("scripts/setup.py").read_text()
    assert "install_python_dependencies" in content
    assert "install_docker_compose" in content
    assert "run_optional_smoke_tests" in content
    assert "check_environment" in content


def test_parse_args_supports_non_interactive_mode_and_overrides():
    args = setup_script.parse_args(
        [
            "--non-interactive",
            "--redis-mode",
            "external",
            "--redis-url",
            "redis://cache.example.com:6379/1",
            "--token",
            "token-123",
            "--webhook-url",
            "https://example.com/hook",
            "--webhook-secret",
            "secret-123",
            "--skip-smoke",
            "--skip-deps",
        ]
    )

    assert args.non_interactive is True
    assert args.redis_mode == "external"
    assert args.redis_url == "redis://cache.example.com:6379/1"
    assert args.token == "token-123"
    assert args.webhook_url == "https://example.com/hook"
    assert args.webhook_secret == "secret-123"
    assert args.skip_smoke is True
    assert args.skip_deps is True


def test_collect_configuration_from_args_returns_expected_values():
    args = setup_script.parse_args(
        [
            "--non-interactive",
            "--redis-mode",
            "skip",
            "--token",
            "token-123",
            "--webhook-secret",
            "secret-123",
        ]
    )

    config = setup_script.collect_configuration_from_args(args)

    assert config.redis_mode == "skip"
    assert config.redis_url == ""
    assert config.token == "token-123"
    assert config.webhook_url == ""
    assert config.webhook_secret == "secret-123"


def test_collect_configuration_from_args_requires_https_webhook_url():
    args = setup_script.parse_args(
        [
            "--non-interactive",
            "--redis-mode",
            "skip",
            "--token",
            "token-123",
            "--webhook-url",
            "http://example.com/hook",
        ]
    )

    try:
        setup_script.collect_configuration_from_args(args)
    except ValueError as exc:
        assert "https://" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid webhook URL")


def test_main_non_interactive_writes_env_without_prompts(monkeypatch, tmp_path):
    root = tmp_path
    src = root / "src"
    src.mkdir()
    (root / "scripts").mkdir()

    monkeypatch.setattr(setup_script, "ROOT", root)
    monkeypatch.setattr(setup_script, "check_environment", lambda: EnvironmentStatus(True, True, True, False, False, False, "apt-get", "docker unavailable"))
    monkeypatch.setattr(setup_script, "print_environment_summary", lambda env_status: None)
    monkeypatch.setattr(setup_script, "install_python_dependencies", lambda: True)
    smoke_calls = []
    monkeypatch.setattr(setup_script, "run_optional_smoke_tests", lambda redis_url, auto_confirm=False: smoke_calls.append((redis_url, auto_confirm)))

    prompt_fail = AssertionError("interactive prompt should not be used in non-interactive mode")
    monkeypatch.setattr(setup_script, "ask", lambda *args, **kwargs: (_ for _ in ()).throw(prompt_fail))
    monkeypatch.setattr(setup_script, "ask_yes_no", lambda *args, **kwargs: (_ for _ in ()).throw(prompt_fail))
    monkeypatch.setattr(setup_script, "ask_secret", lambda *args, **kwargs: (_ for _ in ()).throw(prompt_fail))

    setup_script.main(
        [
            "--non-interactive",
            "--redis-mode",
            "skip",
            "--token",
            "token-123",
            "--webhook-secret",
            "secret-123",
            "--skip-smoke",
        ]
    )

    env_content = (root / ".env").read_text()
    assert "MAX_BOT_TOKEN=token-123" in env_content
    assert "MAX_WEBHOOK_SECRET=secret-123" in env_content
    assert "REDIS_URL=" in env_content
    assert smoke_calls == []


def test_prompt_webhook_url_retries_until_https(monkeypatch):
    answers = iter(["y", "http://bad.example.com/hook", "https://good.example.com/hook"])
    monkeypatch.setattr(setup_script, "ask_yes_no", lambda *args, **kwargs: next(answers) == "y")
    monkeypatch.setattr(setup_script, "ask", lambda *args, **kwargs: next(answers))

    assert setup_script.prompt_webhook_url() == "https://good.example.com/hook"


def test_run_optional_smoke_tests_can_auto_confirm(monkeypatch, tmp_path):
    root = tmp_path
    venv_bin = root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").write_text("#!/bin/sh\n")

    monkeypatch.setattr(setup_script, "ROOT", root)
    calls = []
    monkeypatch.setattr(setup_script, "run", lambda cmd: calls.append(cmd) or CommandResult(True, "ok"))

    setup_script.run_optional_smoke_tests("redis://localhost:6379/0", auto_confirm=True)

    assert calls == [
        [str(venv_bin / "python"), "scripts/redis_smoke.py"],
        [str(venv_bin / "python"), "scripts/live_outbound_smoke.py"],
    ]


def test_main_non_interactive_local_redis_starts_compose(monkeypatch, tmp_path):
    root = tmp_path
    (root / "scripts").mkdir()

    monkeypatch.setattr(setup_script, "ROOT", root)
    monkeypatch.setattr(
        setup_script,
        "check_environment",
        lambda: EnvironmentStatus(True, True, True, True, True, True, "apt-get", "Docker Compose and daemon access are available."),
    )
    monkeypatch.setattr(setup_script, "print_environment_summary", lambda env_status: None)
    monkeypatch.setattr(setup_script, "install_python_dependencies", lambda: True)
    monkeypatch.setattr(setup_script, "run_optional_smoke_tests", lambda redis_url, auto_confirm=False: None)

    calls = []

    def fake_run(cmd):
        calls.append(cmd)
        if cmd == ["docker", "compose", "up", "-d", "redis"]:
            return CommandResult(True, "started")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(setup_script, "run", fake_run)

    setup_script.main(
        [
            "--non-interactive",
            "--redis-mode",
            "local",
            "--token",
            "token-123",
            "--skip-smoke",
            "--skip-deps",
        ]
    )

    env_content = (root / ".env").read_text()
    assert "REDIS_URL=redis://localhost:6379/0" in env_content
    assert ["docker", "compose", "up", "-d", "redis"] in calls


def test_main_non_interactive_local_redis_exits_on_compose_failure(monkeypatch, tmp_path, capsys):
    root = tmp_path
    (root / "scripts").mkdir()

    monkeypatch.setattr(setup_script, "ROOT", root)
    monkeypatch.setattr(
        setup_script,
        "check_environment",
        lambda: EnvironmentStatus(True, True, True, True, True, True, "apt-get", "Docker Compose and daemon access are available."),
    )
    monkeypatch.setattr(setup_script, "print_environment_summary", lambda env_status: None)
    monkeypatch.setattr(setup_script, "install_python_dependencies", lambda: True)
    monkeypatch.setattr(
        setup_script,
        "run",
        lambda cmd: CommandResult(False, "compose failed") if cmd == ["docker", "compose", "up", "-d", "redis"] else CommandResult(True, "ok"),
    )

    try:
        setup_script.main(
            [
                "--non-interactive",
                "--redis-mode",
                "local",
                "--token",
                "token-123",
                "--skip-smoke",
                "--skip-deps",
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected SystemExit when local Redis bootstrap fails")

    captured = capsys.readouterr()
    assert "compose failed" in captured.out
    assert "local redis" in captured.out.lower()


def test_parse_args_supports_dry_run_and_json_flags():
    args = setup_script.parse_args(["--non-interactive", "--token", "token-123", "--dry-run", "--json"])
    assert args.dry_run is True
    assert args.json is True


def test_main_dry_run_does_not_write_env_or_run_smoke(monkeypatch, tmp_path, capsys):
    root = tmp_path
    (root / "scripts").mkdir()

    monkeypatch.setattr(setup_script, "ROOT", root)
    monkeypatch.setattr(setup_script, "check_environment", lambda: EnvironmentStatus(True, True, True, False, False, False, "apt-get", "docker unavailable"))
    monkeypatch.setattr(setup_script, "print_environment_summary", lambda env_status: None)
    monkeypatch.setattr(setup_script, "install_python_dependencies", lambda: True)

    smoke_calls = []
    monkeypatch.setattr(setup_script, "run_optional_smoke_tests", lambda redis_url, auto_confirm=False: smoke_calls.append((redis_url, auto_confirm)))

    setup_script.main(
        [
            "--non-interactive",
            "--redis-mode",
            "skip",
            "--token",
            "token-123",
            "--webhook-secret",
            "secret-123",
            "--dry-run",
        ]
    )

    assert not (root / ".env").exists()
    assert smoke_calls == []
    captured = capsys.readouterr()
    assert "dry-run" in captured.out.lower()


def test_main_json_mode_prints_machine_readable_summary(monkeypatch, tmp_path, capsys):
    root = tmp_path
    (root / "scripts").mkdir()

    monkeypatch.setattr(setup_script, "ROOT", root)
    monkeypatch.setattr(setup_script, "check_environment", lambda: EnvironmentStatus(True, True, True, False, False, False, "apt-get", "docker unavailable"))
    monkeypatch.setattr(setup_script, "print_environment_summary", lambda env_status: None)
    monkeypatch.setattr(setup_script, "install_python_dependencies", lambda: True)
    monkeypatch.setattr(setup_script, "run_optional_smoke_tests", lambda redis_url, auto_confirm=False: None)

    setup_script.main(
        [
            "--non-interactive",
            "--redis-mode",
            "skip",
            "--token",
            "token-123",
            "--webhook-secret",
            "secret-123",
            "--skip-smoke",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert '"status": "ok"' in captured.out
    assert '"redis_mode": "skip"' in captured.out
    assert '"env_written": true' in captured.out


def test_main_invalid_cli_configuration_exits_with_code_3_and_json_error(monkeypatch, tmp_path, capsys):
    root = tmp_path
    (root / "scripts").mkdir()

    monkeypatch.setattr(setup_script, "ROOT", root)
    monkeypatch.setattr(setup_script, "check_environment", lambda: EnvironmentStatus(True, True, True, False, False, False, "apt-get", "docker unavailable"))
    monkeypatch.setattr(setup_script, "print_environment_summary", lambda env_status: None)
    monkeypatch.setattr(setup_script, "install_python_dependencies", lambda: True)

    try:
        setup_script.main(
            [
                "--non-interactive",
                "--redis-mode",
                "skip",
                "--token",
                "token-123",
                "--webhook-url",
                "http://bad.example.com/hook",
                "--json",
                "--skip-deps",
            ]
        )
    except SystemExit as exc:
        assert exc.code == 3
    else:
        raise AssertionError("Expected SystemExit(3) for invalid CLI configuration")

    captured = capsys.readouterr()
    assert '"status": "error"' in captured.out
    assert '"exit_code": 3' in captured.out


def test_main_bootstrap_failure_in_json_mode_exits_with_code_2(monkeypatch, tmp_path, capsys):
    root = tmp_path
    (root / "scripts").mkdir()

    monkeypatch.setattr(setup_script, "ROOT", root)
    monkeypatch.setattr(
        setup_script,
        "check_environment",
        lambda: EnvironmentStatus(True, True, True, True, True, True, "apt-get", "Docker Compose and daemon access are available."),
    )
    monkeypatch.setattr(setup_script, "print_environment_summary", lambda env_status: None)
    monkeypatch.setattr(setup_script, "install_python_dependencies", lambda: True)
    monkeypatch.setattr(
        setup_script,
        "run",
        lambda cmd: CommandResult(False, "compose failed") if cmd == ["docker", "compose", "up", "-d", "redis"] else CommandResult(True, "ok"),
    )

    try:
        setup_script.main(
            [
                "--non-interactive",
                "--redis-mode",
                "local",
                "--token",
                "token-123",
                "--json",
                "--skip-deps",
                "--skip-smoke",
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected SystemExit(2) for bootstrap failure")

    captured = capsys.readouterr()
    assert '"status": "error"' in captured.out
    assert '"exit_code": 2' in captured.out
