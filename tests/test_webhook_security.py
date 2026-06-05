from hermes_max_adapter.webhook_server import handle_webhook, validate_secret


def test_validate_secret_accepts_matching_header():
    assert validate_secret("abc", "abc") is True


def test_validate_secret_rejects_mismatch():
    assert validate_secret("abc", "xyz") is False


def test_handle_webhook_returns_200_and_enqueues_when_secret_matches():
    calls: list[bytes] = []

    def enqueue(body: bytes) -> None:
        calls.append(body)

    status_code, body = handle_webhook("abc", "abc", b'{"ok": true}', enqueue)
    assert status_code == 200
    assert body == "ok"
    assert calls == [b'{"ok": true}']


def test_handle_webhook_returns_401_when_secret_invalid():
    calls: list[bytes] = []

    def enqueue(body: bytes) -> None:
        calls.append(body)

    status_code, body = handle_webhook("abc", "wrong", b'{}', enqueue)
    assert status_code == 401
    assert body == "unauthorized"
    assert calls == []
