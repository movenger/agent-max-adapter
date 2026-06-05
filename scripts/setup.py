from __future__ import annotations

import argparse
import getpass
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hermes_max_adapter.setup_lib import (
    DEFAULTS,
    diagnose_docker_access,
    is_valid_https_url,
    is_valid_redis_url,
    render_env_file,
    select_package_manager,
)


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    output: str


@dataclass(frozen=True)
class EnvironmentStatus:
    python_ok: bool
    venv_active: bool
    pip_ok: bool
    docker_ok: bool
    compose_ok: bool
    docker_daemon_ok: bool
    package_manager: str | None
    docker_message: str


@dataclass(frozen=True)
class SetupConfig:
    redis_mode: str
    redis_url: str
    token: str
    webhook_url: str
    webhook_secret: str


EXIT_BOOTSTRAP_FAILURE = 2
EXIT_INVALID_CONFIGURATION = 3


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hermes MAX Adapter setup wizard")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--redis-mode", choices=["local", "external", "skip"])
    parser.add_argument("--redis-url")
    parser.add_argument("--token")
    parser.add_argument("--webhook-url")
    parser.add_argument("--webhook-secret")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--skip-deps", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def ask_secret(prompt: str) -> str:
    return getpass.getpass(f"{prompt}: ").strip()


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    marker = "Y/n" if default else "y/N"
    value = input(f"{prompt} [{marker}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes"}


def choose_menu(prompt: str, options: list[tuple[str, str]], default_key: str) -> str:
    print(prompt)
    keys = {key for key, _ in options}
    for key, label in options:
        default_marker = " (default)" if key == default_key else ""
        print(f"  {key}. {label}{default_marker}")
    while True:
        choice = input("Choose an option: ").strip() or default_key
        if choice in keys:
            return choice
        print("Invalid choice. Please enter one of:", ", ".join(sorted(keys)))


def run(cmd: list[str]) -> CommandResult:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return CommandResult(ok=proc.returncode == 0, output=output)


def run_shell(command: str) -> CommandResult:
    proc = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=ROOT)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return CommandResult(ok=proc.returncode == 0, output=output)


def check_environment() -> EnvironmentStatus:
    python_ok = shutil.which("python3") is not None or shutil.which("python") is not None
    pip_ok = shutil.which("pip") is not None or shutil.which("pip3") is not None
    docker_ok = shutil.which("docker") is not None
    compose_result = run(["docker", "compose", "version"]) if docker_ok else CommandResult(False, "docker not found")
    daemon_result = run(["docker", "info"]) if docker_ok else CommandResult(False, "docker not found")
    package_manager = select_package_manager(
        {
            "apt-get": shutil.which("apt-get"),
            "brew": shutil.which("brew"),
            "dnf": shutil.which("dnf"),
            "yum": shutil.which("yum"),
        }
    )
    venv_active = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    diagnosis = diagnose_docker_access(
        compose_available=compose_result.ok,
        daemon_check_ok=daemon_result.ok,
        daemon_output=daemon_result.output or compose_result.output,
    )
    return EnvironmentStatus(
        python_ok=python_ok,
        venv_active=venv_active,
        pip_ok=pip_ok,
        docker_ok=docker_ok,
        compose_ok=compose_result.ok,
        docker_daemon_ok=daemon_result.ok,
        package_manager=package_manager,
        docker_message=diagnosis.message,
    )


def install_python_dependencies() -> bool:
    venv_dir = ROOT / ".venv"
    if not venv_dir.exists():
        print("Creating virtual environment...")
        result = run([sys.executable, "-m", "venv", str(venv_dir)])
        if not result.ok:
            print(result.output)
            return False

    pip_path = venv_dir / "bin" / "pip"
    if not pip_path.exists():
        print("Virtualenv created but pip was not found inside .venv/bin/pip")
        return False

    print("Installing Python dependencies into .venv...")
    result = run([str(pip_path), "install", "-e", ".", "pytest"])
    if not result.ok:
        print(result.output)
        return False
    return True


def install_docker_compose(package_manager: str | None) -> bool:
    if not package_manager:
        print("No supported package manager found for Docker Compose installation.")
        return False

    commands = {
        "apt-get": "sudo apt-get update && sudo apt-get install -y docker-compose-plugin",
        "brew": "brew install docker-compose",
        "dnf": "sudo dnf install -y docker-compose-plugin",
        "yum": "sudo yum install -y docker-compose-plugin",
    }
    command = commands[package_manager]
    print(f"Installing Docker Compose via {package_manager}...")
    result = run_shell(command)
    if not result.ok:
        print(result.output)
        return False
    return True


def install_docker_engine(package_manager: str | None) -> bool:
    if not package_manager:
        print("No supported package manager found for Docker Engine installation.")
        return False

    commands = {
        "apt-get": "sudo apt-get update && sudo apt-get install -y docker.io",
        "brew": "brew install --cask docker",
        "dnf": "sudo dnf install -y docker",
        "yum": "sudo yum install -y docker",
    }
    command = commands[package_manager]
    print(f"Installing Docker via {package_manager}...")
    result = run_shell(command)
    if not result.ok:
        print(result.output)
        return False
    return True


def ensure_docker_group_access() -> bool:
    user = getpass.getuser()
    print(f"Attempting to add {user} to the docker group...")
    result = run_shell(f"sudo usermod -aG docker {user}")
    if not result.ok:
        print(result.output)
        return False
    print("Docker group membership updated. You may need to log out and back in.")
    return True


def prompt_redis_mode(env_status: EnvironmentStatus) -> tuple[str, str]:
    choice = choose_menu(
        "Redis mode:",
        [
            ("1", "Local Redis via Docker Compose"),
            ("2", "External Redis URL"),
            ("3", "Skip Redis for now"),
        ],
        default_key="1",
    )

    if choice == "1":
        if not env_status.docker_ok and ask_yes_no("Docker is not installed. Try to install it now?", default=True):
            if not install_docker_engine(env_status.package_manager):
                return prompt_redis_mode(check_environment())
            env_status = check_environment()

        if not env_status.compose_ok and ask_yes_no("Docker Compose is not available. Try to install it now?", default=True):
            if not install_docker_compose(env_status.package_manager):
                return prompt_redis_mode(check_environment())
            env_status = check_environment()

        diagnosis = diagnose_docker_access(
            compose_available=env_status.compose_ok,
            daemon_check_ok=env_status.docker_daemon_ok,
            daemon_output=env_status.docker_message,
        )
        if diagnosis.status == "permission_denied":
            print(diagnosis.message)
            if ask_yes_no("Try to grant docker group access now?", default=False):
                ensure_docker_group_access()
            print("Falling back to external/skip Redis until Docker daemon access works.")
            return prompt_redis_mode(EnvironmentStatus(**{**env_status.__dict__, "compose_ok": False}))

        if diagnosis.status in {"missing_compose", "daemon_unreachable", "unknown_error"}:
            print(diagnosis.message)
            print("Falling back to external/skip Redis.")
            return prompt_redis_mode(EnvironmentStatus(**{**env_status.__dict__, "compose_ok": False}))

        print("Starting local Redis with docker compose...")
        result = run(["docker", "compose", "up", "-d", "redis"])
        if result.ok:
            return "local", DEFAULTS["REDIS_URL"]
        print("Could not start local Redis automatically.")
        print(result.output)
        print("Falling back to external/skip Redis.")
        return prompt_redis_mode(EnvironmentStatus(**{**env_status.__dict__, "compose_ok": False}))

    if choice == "2":
        while True:
            redis_url = ask("Enter REDIS_URL", DEFAULTS["REDIS_URL"])
            if is_valid_redis_url(redis_url):
                return "external", redis_url
            print("REDIS_URL must start with redis:// or rediss:// and include a host.")

    return "skip", ""


def prompt_webhook_url() -> str:
    has_webhook = ask_yes_no("Do you already have a public webhook URL?", default=False)
    if not has_webhook:
        return ""

    while True:
        webhook_url = ask("Enter MAX_WEBHOOK_URL")
        if is_valid_https_url(webhook_url):
            return webhook_url
        print("Webhook URL must start with https:// and include a host.")


def emit_error(*, message: str, exit_code: int, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps({"status": "error", "exit_code": exit_code, "message": message}))
    else:
        print(message)


def emit_success_summary(*, config: SetupConfig, env_written: bool, dry_run: bool, json_mode: bool) -> None:
    if json_mode:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "redis_mode": config.redis_mode,
                    "redis_url": config.redis_url,
                    "webhook_mode": "webhook-ready" if config.webhook_url else "token-only",
                    "webhook_url": config.webhook_url,
                    "env_written": env_written,
                    "dry_run": dry_run,
                }
            )
        )
        return

    if dry_run:
        print("Dry-run mode: configuration was validated but .env was not written and smoke checks were skipped.")
        return

    print()
    print(f"Wrote {ROOT / '.env'}")
    print("Configuration summary:")
    print(f"- Redis mode: {config.redis_mode}")
    print(f"- Redis URL: {config.redis_url or '(disabled)'}")
    print(f"- Webhook mode: {'webhook-ready' if config.webhook_url else 'token-only'}")
    print(f"- Webhook URL: {config.webhook_url or '(not set)'}")
    print()
    print("Next steps:")
    if config.redis_url:
        print("- Run: . .venv/bin/activate && python scripts/redis_smoke.py")
    print("- Run: . .venv/bin/activate && python scripts/live_outbound_smoke.py")


def ensure_local_redis_ready_non_interactive(env_status: EnvironmentStatus) -> str:
    diagnosis = diagnose_docker_access(
        compose_available=env_status.compose_ok,
        daemon_check_ok=env_status.docker_daemon_ok,
        daemon_output=env_status.docker_message,
    )

    if not env_status.docker_ok:
        raise RuntimeError("Local Redis bootstrap failed: Docker is not installed or not available in PATH.")

    if diagnosis.status != "ok":
        raise RuntimeError(f"Local Redis bootstrap failed: {diagnosis.message}")

    print("Starting local Redis with docker compose...")
    result = run(["docker", "compose", "up", "-d", "redis"])
    if not result.ok:
        raise RuntimeError(f"Local Redis bootstrap failed. {result.output}")

    return DEFAULTS["REDIS_URL"]


def collect_configuration_from_args(
    args: argparse.Namespace,
    env_status: EnvironmentStatus | None = None,
) -> SetupConfig:
    if not args.token:
        raise ValueError("--token is required in --non-interactive mode")

    redis_mode = args.redis_mode or "skip"
    redis_url = ""
    if redis_mode == "local":
        if env_status is None:
            raise ValueError("env_status is required when --redis-mode local is used")
        redis_url = ensure_local_redis_ready_non_interactive(env_status)
    elif redis_mode == "external":
        redis_url = args.redis_url or DEFAULTS["REDIS_URL"]
        if not is_valid_redis_url(redis_url):
            raise ValueError("External Redis URL must start with redis:// or rediss://")

    webhook_url = args.webhook_url or ""
    if webhook_url and not is_valid_https_url(webhook_url):
        raise ValueError("Webhook URL must start with https:// and include a host")

    return SetupConfig(
        redis_mode=redis_mode,
        redis_url=redis_url,
        token=args.token,
        webhook_url=webhook_url,
        webhook_secret=args.webhook_secret or DEFAULTS["MAX_WEBHOOK_SECRET"],
    )


def collect_interactive_configuration() -> SetupConfig:
    redis_mode, redis_url = prompt_redis_mode(check_environment())
    token = ask_secret("Enter MAX_BOT_TOKEN")
    webhook_url = prompt_webhook_url()
    webhook_secret = ask("Enter MAX_WEBHOOK_SECRET", DEFAULTS["MAX_WEBHOOK_SECRET"])
    return SetupConfig(
        redis_mode=redis_mode,
        redis_url=redis_url,
        token=token,
        webhook_url=webhook_url,
        webhook_secret=webhook_secret,
    )


def run_optional_smoke_tests(redis_url: str, auto_confirm: bool = False) -> None:
    if not auto_confirm and not ask_yes_no("Run smoke checks now?", default=True):
        return

    python_bin = ROOT / ".venv" / "bin" / "python"
    runner = str(python_bin if python_bin.exists() else Path(sys.executable))

    if redis_url:
        print("Running Redis smoke...")
        result = run([runner, "scripts/redis_smoke.py"])
        print(result.output or "Redis smoke finished without output.")

    print("Running live outbound smoke...")
    result = run([runner, "scripts/live_outbound_smoke.py"])
    print(result.output or "Live outbound smoke finished without output.")


def print_environment_summary(env_status: EnvironmentStatus) -> None:
    print("Environment check:")
    print(f"- Python available: {'yes' if env_status.python_ok else 'no'}")
    print(f"- Virtualenv active: {'yes' if env_status.venv_active else 'no'}")
    print(f"- pip available: {'yes' if env_status.pip_ok else 'no'}")
    print(f"- Docker available: {'yes' if env_status.docker_ok else 'no'}")
    print(f"- Docker Compose available: {'yes' if env_status.compose_ok else 'no'}")
    print(f"- Docker daemon access: {'yes' if env_status.docker_daemon_ok else 'no'}")
    if env_status.docker_message:
        print(f"- Docker note: {env_status.docker_message}")
    if env_status.package_manager:
        print(f"- Package manager: {env_status.package_manager}")
    print()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    print("Hermes MAX Adapter Setup Wizard")
    print()

    env_status = check_environment()
    print_environment_summary(env_status)

    if not args.skip_deps:
        if args.non_interactive:
            install_python_dependencies()
        elif ask_yes_no("Create/update .venv and install Python dependencies?", default=True):
            install_python_dependencies()

    try:
        config = collect_configuration_from_args(args, env_status) if args.non_interactive else collect_interactive_configuration()
    except ValueError as exc:
        emit_error(message=str(exc), exit_code=EXIT_INVALID_CONFIGURATION, json_mode=args.json)
        raise SystemExit(EXIT_INVALID_CONFIGURATION) from exc
    except RuntimeError as exc:
        emit_error(message=str(exc), exit_code=EXIT_BOOTSTRAP_FAILURE, json_mode=args.json)
        raise SystemExit(EXIT_BOOTSTRAP_FAILURE) from exc

    env_content = render_env_file(
        {
            "MAX_BOT_TOKEN": config.token,
            "MAX_WEBHOOK_SECRET": config.webhook_secret,
            "MAX_WEBHOOK_URL": config.webhook_url,
            "REDIS_URL": config.redis_url,
        }
    )

    env_written = False
    if not args.dry_run:
        env_path = ROOT / ".env"
        env_path.write_text(env_content)
        env_written = True

    emit_success_summary(config=config, env_written=env_written, dry_run=args.dry_run, json_mode=args.json)

    if not args.skip_smoke and not args.dry_run:
        run_optional_smoke_tests(config.redis_url, auto_confirm=args.non_interactive)


if __name__ == "__main__":
    main()
