from hermes_max_adapter.setup_lib import (
    diagnose_docker_access,
    is_valid_https_url,
    is_valid_redis_url,
    render_env_file,
    select_package_manager,
)


def test_render_env_file_for_token_only_mode():
    content = render_env_file(
        {
            "MAX_BOT_TOKEN": "token",
            "MAX_WEBHOOK_SECRET": "dev-secret",
            "MAX_WEBHOOK_URL": "",
            "REDIS_URL": "redis://localhost:6379/0",
        }
    )
    assert "MAX_BOT_TOKEN=token" in content
    assert "REDIS_URL=redis://localhost:6379/0" in content


def test_select_package_manager_prefers_apt_then_brew_then_dnf_then_yum():
    assert select_package_manager({"apt-get": "/usr/bin/apt-get", "brew": "/opt/homebrew/bin/brew"}) == "apt-get"
    assert select_package_manager({"brew": "/opt/homebrew/bin/brew"}) == "brew"
    assert select_package_manager({"dnf": "/usr/bin/dnf"}) == "dnf"
    assert select_package_manager({"yum": "/usr/bin/yum"}) == "yum"
    assert select_package_manager({}) is None


def test_https_url_validation_accepts_only_https_urls():
    assert is_valid_https_url("https://example.com/webhook") is True
    assert is_valid_https_url("http://example.com/webhook") is False
    assert is_valid_https_url("example.com/webhook") is False
    assert is_valid_https_url("") is False


def test_redis_url_validation_requires_redis_or_rediss_scheme():
    assert is_valid_redis_url("redis://localhost:6379/0") is True
    assert is_valid_redis_url("rediss://cache.example.com:6379/1") is True
    assert is_valid_redis_url("http://localhost:6379/0") is False
    assert is_valid_redis_url("localhost:6379") is False


def test_diagnose_docker_access_identifies_permission_denied():
    result = diagnose_docker_access(
        compose_available=True,
        daemon_check_ok=False,
        daemon_output="permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock",
    )
    assert result.status == "permission_denied"
    assert "docker.sock" in result.message


def test_diagnose_docker_access_identifies_missing_compose():
    result = diagnose_docker_access(
        compose_available=False,
        daemon_check_ok=False,
        daemon_output="docker: 'compose' is not a docker command",
    )
    assert result.status == "missing_compose"


def test_diagnose_docker_access_identifies_unavailable_daemon():
    result = diagnose_docker_access(
        compose_available=True,
        daemon_check_ok=False,
        daemon_output="Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?",
    )
    assert result.status == "daemon_unreachable"


def test_diagnose_docker_access_ok_when_compose_and_daemon_are_available():
    result = diagnose_docker_access(
        compose_available=True,
        daemon_check_ok=True,
        daemon_output="Docker version 27.0.0",
    )
    assert result.status == "ok"
