from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse

ENV_KEYS = [
    "MAX_BOT_TOKEN",
    "MAX_WEBHOOK_SECRET",
    "MAX_WEBHOOK_URL",
    "MAX_ENABLE_LONG_POLLING",
    "MAX_MAX_RETRIES",
    "MAX_RETRY_BACKOFF_SECONDS",
    "MAX_REQUEST_TIMEOUT_SECONDS",
    "REDIS_URL",
    "MAX_DEDUPE_TTL_SECONDS",
    "LOCAL_WEBHOOK_PORT",
]

DEFAULTS = {
    "MAX_BOT_TOKEN": "",
    "MAX_WEBHOOK_SECRET": "dev-secret",
    "MAX_WEBHOOK_URL": "",
    "MAX_ENABLE_LONG_POLLING": "false",
    "MAX_MAX_RETRIES": "2",
    "MAX_RETRY_BACKOFF_SECONDS": "0",
    "MAX_REQUEST_TIMEOUT_SECONDS": "15",
    "REDIS_URL": "redis://localhost:6379/0",
    "MAX_DEDUPE_TTL_SECONDS": "3600",
    "LOCAL_WEBHOOK_PORT": "18080",
}


@dataclass(frozen=True)
class DockerAccessDiagnosis:
    status: str
    message: str


def render_env_file(overrides: Mapping[str, str]) -> str:
    merged = {**DEFAULTS, **dict(overrides)}
    lines = [f"{key}={merged.get(key, '')}" for key in ENV_KEYS]
    return "\n".join(lines) + "\n"


def select_package_manager(commands: Mapping[str, str | None]) -> str | None:
    for name in ("apt-get", "brew", "dnf", "yum"):
        if commands.get(name):
            return name
    return None


def is_valid_https_url(value: str) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def is_valid_redis_url(value: str) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"redis", "rediss"} and bool(parsed.netloc)


def diagnose_docker_access(
    *,
    compose_available: bool,
    daemon_check_ok: bool,
    daemon_output: str,
) -> DockerAccessDiagnosis:
    normalized = daemon_output.lower()

    if not compose_available:
        return DockerAccessDiagnosis(
            status="missing_compose",
            message="Docker Compose plugin is not available.",
        )

    if daemon_check_ok:
        return DockerAccessDiagnosis(
            status="ok",
            message="Docker Compose and daemon access are available.",
        )

    if "cannot connect to the docker daemon" in normalized or "is the docker daemon running" in normalized:
        return DockerAccessDiagnosis(
            status="daemon_unreachable",
            message="Docker daemon is not reachable.",
        )

    if "permission denied" in normalized:
        return DockerAccessDiagnosis(
            status="permission_denied",
            message="Docker daemon access failed: permission denied on docker.sock.",
        )

    return DockerAccessDiagnosis(
        status="unknown_error",
        message=daemon_output.strip() or "Unknown Docker access failure.",
    )
