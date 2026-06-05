from __future__ import annotations

import hmac
from collections.abc import Callable


def validate_secret(expected: str, provided: str | None) -> bool:
    if not expected:
        return True
    if not provided:
        return False
    return hmac.compare_digest(expected, provided)


def handle_webhook(
    expected_secret: str,
    provided_secret: str | None,
    body: bytes,
    enqueue: Callable[[bytes], None],
) -> tuple[int, str]:
    if not validate_secret(expected_secret, provided_secret):
        return 401, "unauthorized"
    enqueue(body)
    return 200, "ok"


def dispatch_webhook_to_adapter(adapter: object, payload: dict) -> dict:
    return adapter.process_update(payload)
