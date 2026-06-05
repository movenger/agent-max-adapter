# Hermes MAX Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить production-grade plugin-based интеграцию MAX Bot API с Hermes Agent как полноценный канал Hermes.

**Architecture:** Реализация идёт через Hermes plugin system и `BasePlatformAdapter`. Production ingress — только Webhook: быстрый `200 OK`, асинхронная обработка, dedupe, rate-limited outbound MAX client, deterministic session mapping и operational hardening.

**Tech Stack:** Python 3.12+, Hermes Agent plugin system, async HTTP client, pytest, optional Redis for dedupe/state.

---

## File structure

### New files
- `README.md`
- `pyproject.toml`
- `src/hermes_max_adapter/__init__.py`
- `src/hermes_max_adapter/plugin.py`
- `src/hermes_max_adapter/adapter.py`
- `src/hermes_max_adapter/config.py`
- `src/hermes_max_adapter/client.py`
- `src/hermes_max_adapter/webhook_server.py`
- `src/hermes_max_adapter/updates.py`
- `src/hermes_max_adapter/mapping.py`
- `src/hermes_max_adapter/renderer.py`
- `src/hermes_max_adapter/rate_limit.py`
- `src/hermes_max_adapter/dedupe.py`
- `src/hermes_max_adapter/observability.py`
- `src/hermes_max_adapter/models/__init__.py`
- `src/hermes_max_adapter/models/max_updates.py`
- `src/hermes_max_adapter/models/max_messages.py`
- `tests/test_updates.py`
- `tests/test_renderer.py`
- `tests/test_dedupe.py`
- `tests/test_webhook_security.py`
- `tests/test_send_chunking.py`
- `tests/integration/test_webhook_flow.py`
- `tests/integration/test_callback_flow.py`
- `tests/integration/test_delivery_failures.py`

### Existing files to use as source documents
- `docs/specs/hermes-max-adapter-spec.md`
- `docs/api/max-bot-api-notes.md`
- `docs/research/scout-max-hermes-research.md`

---

### Task 1: Bootstrap Python package and plugin entrypoint

**Files:**
- Create: `pyproject.toml`
- Create: `src/hermes_max_adapter/__init__.py`
- Create: `src/hermes_max_adapter/plugin.py`
- Test: `tests/test_plugin_registration.py`

- [ ] **Step 1: Write the failing test for plugin registration metadata**

```python
from hermes_max_adapter.plugin import build_registration


def test_build_registration_exposes_expected_platform_metadata():
    registration = build_registration()
    assert registration["name"] == "max"
    assert registration["required_env"] == ["MAX_BOT_TOKEN"]
    assert registration["cron_deliver_env_var"] == "MAX_HOME_CHANNEL"
    assert registration["max_message_length"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_registration.py -v`
Expected: FAIL with import or missing symbol error.

- [ ] **Step 3: Write minimal package bootstrap and plugin registration helper**

```python
# src/hermes_max_adapter/__init__.py
__all__ = ["__version__"]
__version__ = "0.1.0"
```

```python
# src/hermes_max_adapter/plugin.py
from __future__ import annotations


def build_registration() -> dict:
    return {
        "name": "max",
        "label": "MAX",
        "required_env": ["MAX_BOT_TOKEN"],
        "cron_deliver_env_var": "MAX_HOME_CHANNEL",
        "max_message_length": 4000,
        "emoji": "💬",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plugin_registration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/hermes_max_adapter/__init__.py src/hermes_max_adapter/plugin.py tests/test_plugin_registration.py
git commit -m "feat: bootstrap hermes max plugin registration"
```

### Task 2: Add config model and env parsing

**Files:**
- Create: `src/hermes_max_adapter/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing config test**

```python
from hermes_max_adapter.config import MaxAdapterConfig


def test_config_reads_required_env_values(monkeypatch):
    monkeypatch.setenv("MAX_BOT_TOKEN", "token")
    monkeypatch.setenv("MAX_WEBHOOK_SECRET", "secret")
    cfg = MaxAdapterConfig.from_env()
    assert cfg.bot_token == "token"
    assert cfg.webhook_secret == "secret"
    assert cfg.enable_long_polling is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL

- [ ] **Step 3: Implement minimal config dataclass**

```python
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class MaxAdapterConfig:
    bot_token: str
    webhook_secret: str
    webhook_url: str | None
    enable_long_polling: bool

    @classmethod
    def from_env(cls) -> "MaxAdapterConfig":
        return cls(
            bot_token=os.getenv("MAX_BOT_TOKEN", "").strip(),
            webhook_secret=os.getenv("MAX_WEBHOOK_SECRET", "").strip(),
            webhook_url=os.getenv("MAX_WEBHOOK_URL", "").strip() or None,
            enable_long_polling=os.getenv("MAX_ENABLE_LONG_POLLING", "false").lower() == "true",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/hermes_max_adapter/config.py tests/test_config.py
git commit -m "feat: add max adapter env config"
```

### Task 3: Implement webhook secret validation and fast ACK contract

**Files:**
- Create: `src/hermes_max_adapter/webhook_server.py`
- Test: `tests/test_webhook_security.py`

- [ ] **Step 1: Write failing tests for webhook secret validation**

```python
from hermes_max_adapter.webhook_server import validate_secret


def test_validate_secret_accepts_matching_header():
    assert validate_secret("abc", "abc") is True


def test_validate_secret_rejects_mismatch():
    assert validate_secret("abc", "xyz") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_webhook_security.py -v`
Expected: FAIL

- [ ] **Step 3: Implement constant-time secret validator**

```python
from __future__ import annotations

import hmac


def validate_secret(expected: str, provided: str | None) -> bool:
    if not expected:
        return True
    if not provided:
        return False
    return hmac.compare_digest(expected, provided)
```

- [ ] **Step 4: Add a handler stub that returns 200 after validation and enqueue call**

```python
def handle_webhook(expected_secret: str, provided_secret: str | None, body: bytes, enqueue) -> tuple[int, str]:
    if not validate_secret(expected_secret, provided_secret):
        return 401, "unauthorized"
    enqueue(body)
    return 200, "ok"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_webhook_security.py -v`
Expected: PASS

### Task 4: Add update models and normalization

**Files:**
- Create: `src/hermes_max_adapter/models/max_updates.py`
- Create: `src/hermes_max_adapter/updates.py`
- Test: `tests/test_updates.py`

- [ ] **Step 1: Write failing normalization tests**

```python
from hermes_max_adapter.updates import normalize_update


def test_normalize_message_created_update():
    event = normalize_update({
        "update_type": "message_created",
        "message": {"body": {"text": "hi"}},
        "chat_id": "chat-1",
        "user_id": "user-1",
    })
    assert event.kind == "message"
    assert event.chat_id == "chat-1"
    assert event.text == "hi"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_updates.py -v`
Expected: FAIL

- [ ] **Step 3: Implement minimal normalized event model**

```python
from dataclasses import dataclass


@dataclass(slots=True)
class NormalizedEvent:
    kind: str
    chat_id: str
    user_id: str
    text: str | None
    update_type: str
```

```python
from hermes_max_adapter.models.max_updates import NormalizedEvent


def normalize_update(payload: dict) -> NormalizedEvent:
    update_type = payload["update_type"]
    if update_type == "message_created":
        return NormalizedEvent(
            kind="message",
            chat_id=str(payload["chat_id"]),
            user_id=str(payload["user_id"]),
            text=payload.get("message", {}).get("body", {}).get("text"),
            update_type=update_type,
        )
    return NormalizedEvent(
        kind="unsupported",
        chat_id=str(payload.get("chat_id", "")),
        user_id=str(payload.get("user_id", "")),
        text=None,
        update_type=update_type,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_updates.py -v`
Expected: PASS

### Task 5: Implement dedupe store API

**Files:**
- Create: `src/hermes_max_adapter/dedupe.py`
- Test: `tests/test_dedupe.py`

- [ ] **Step 1: Write failing dedupe test**

```python
from hermes_max_adapter.dedupe import InMemoryDedupeStore


def test_dedupe_store_marks_second_occurrence_as_duplicate():
    store = InMemoryDedupeStore()
    assert store.seen("message_created:123") is False
    assert store.seen("message_created:123") is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_dedupe.py -v`
Expected: FAIL

- [ ] **Step 3: Implement minimal in-memory dedupe store**

```python
class InMemoryDedupeStore:
    def __init__(self):
        self._keys: set[str] = set()

    def seen(self, key: str) -> bool:
        if key in self._keys:
            return True
        self._keys.add(key)
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_dedupe.py -v`
Expected: PASS

### Task 6: Add outbound renderer and chunking

**Files:**
- Create: `src/hermes_max_adapter/renderer.py`
- Test: `tests/test_send_chunking.py`
- Test: `tests/test_renderer.py`

- [ ] **Step 1: Write failing chunking test**

```python
from hermes_max_adapter.renderer import chunk_text


def test_chunk_text_splits_long_messages():
    text = "a" * 9001
    chunks = chunk_text(text, limit=4000)
    assert len(chunks) == 3
    assert all(len(chunk) <= 4000 for chunk in chunks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_send_chunking.py -v`
Expected: FAIL

- [ ] **Step 3: Implement minimal chunker**

```python
def chunk_text(text: str, limit: int) -> list[str]:
    if limit <= 0 or len(text) <= limit:
        return [text]
    return [text[i:i + limit] for i in range(0, len(text), limit)]
```

- [ ] **Step 4: Add payload renderer**

```python
def render_outbound_payload(text: str, limit: int = 4000) -> list[dict]:
    return [{"text": chunk} for chunk in chunk_text(text, limit=limit)]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_send_chunking.py tests/test_renderer.py -v`
Expected: PASS

### Task 7: Implement MAX API client shell

**Files:**
- Create: `src/hermes_max_adapter/client.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write failing client request-shape test**

```python
from hermes_max_adapter.client import build_send_request


def test_build_send_request_uses_messages_endpoint_and_auth_header():
    request = build_send_request(
        base_url="https://platform-api.max.ru",
        token="secret",
        user_id="42",
        payload={"text": "hi"},
    )
    assert request["method"] == "POST"
    assert request["url"] == "https://platform-api.max.ru/messages?user_id=42"
    assert request["headers"]["Authorization"] == "secret"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_client.py -v`
Expected: FAIL

- [ ] **Step 3: Implement request builder**

```python
from urllib.parse import urlencode


def build_send_request(base_url: str, token: str, user_id: str | None, payload: dict, chat_id: str | None = None) -> dict:
    params = {}
    if user_id is not None:
        params["user_id"] = user_id
    if chat_id is not None:
        params["chat_id"] = chat_id
    query = urlencode(params)
    return {
        "method": "POST",
        "url": f"{base_url}/messages?{query}" if query else f"{base_url}/messages",
        "headers": {
            "Authorization": token,
            "Content-Type": "application/json",
        },
        "json": payload,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_client.py -v`
Expected: PASS

### Task 8: Implement adapter skeleton against Hermes contract

**Files:**
- Create: `src/hermes_max_adapter/adapter.py`
- Test: `tests/test_adapter.py`

- [ ] **Step 1: Write failing adapter behavior test**

```python
from hermes_max_adapter.adapter import MaxAdapter


def test_adapter_connect_marks_adapter_ready():
    adapter = MaxAdapter(config=None)
    assert adapter.connected is False
    assert adapter.connect_sync() is True
    assert adapter.connected is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: Implement minimal adapter shell**

```python
class MaxAdapter:
    def __init__(self, config):
        self.config = config
        self.connected = False

    def connect_sync(self) -> bool:
        self.connected = True
        return True

    def disconnect_sync(self) -> None:
        self.connected = False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_adapter.py -v`
Expected: PASS

### Task 9: Add integration tests for webhook flow and duplicate handling

**Files:**
- Test: `tests/integration/test_webhook_flow.py`
- Test: `tests/integration/test_delivery_failures.py`

- [ ] **Step 1: Write failing end-to-end webhook flow test**

```python
from hermes_max_adapter.dedupe import InMemoryDedupeStore
from hermes_max_adapter.updates import normalize_update


def test_duplicate_update_processed_once():
    store = InMemoryDedupeStore()
    payload = {
        "update_type": "message_created",
        "chat_id": "c1",
        "user_id": "u1",
        "message": {"body": {"text": "hello"}},
        "mid": "m1",
    }
    key = f"{payload['update_type']}:{payload['mid']}"
    assert store.seen(key) is False
    assert normalize_update(payload).text == "hello"
    assert store.seen(key) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_webhook_flow.py -v`
Expected: FAIL initially until imports and helpers are wired.

- [ ] **Step 3: Wire missing helpers and test fixtures**

```python
# Add reusable helper where needed

def build_dedupe_key(payload: dict) -> str:
    marker = payload.get("mid") or payload.get("message", {}).get("mid") or "unknown"
    return f"{payload.get('update_type', 'unknown')}:{marker}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_webhook_flow.py -v`
Expected: PASS

### Task 10: Polish docs and verify full test suite

**Files:**
- Create: `README.md`
- Modify: `docs/api/max-bot-api-notes.md`
- Modify: `docs/specs/hermes-max-adapter-spec.md`

- [ ] **Step 1: Write README with setup, env, and deployment model**

```md
# Hermes MAX Adapter

Plugin-based MAX Bot API integration for Hermes Agent.

## Production model
- MAX inbound: Webhook only
- HTTPS on port 443
- Secret validation via `X-Max-Bot-Api-Secret`
- Async processing after fast 200 OK
```

- [ ] **Step 2: Run the full test suite**

Run: `pytest tests -v`
Expected: PASS

- [ ] **Step 3: Run a quick file listing sanity check**

Run: `find src tests docs -maxdepth 3 -type f | sort`
Expected: shows all planned implementation and documentation artifacts.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/api/max-bot-api-notes.md docs/specs/hermes-max-adapter-spec.md src tests
git commit -m "docs: finalize max adapter spec and implementation skeleton"
```

---

## Self-review

- Spec coverage: plan covers plugin path, webhook security, dedupe, outbound send, chunking, session-safe scaffolding, tests, docs.
- Placeholder scan: open questions remain in spec, not in execution tasks.
- Type consistency: normalize event, config, dedupe, renderer, client, and adapter naming are consistent across tasks.
