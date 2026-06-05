# Full Production Message Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перевести `hermes-max-adapter` с text-first foundation на production-shaped canonical message/event architecture с backward-compatible text path, capability/degradation surfaces и расширенной тестовой матрицей.

**Architecture:** Сначала вводим typed canonical models и compatibility wrappers, потом расширяем inbound/outbound pipeline под callback/media/button/capability контракты, не ломая текущий text send path. Везде идти через TDD: red → green → refactor.

**Tech Stack:** Python 3.12, pytest, setuptools, existing Hermes MAX adapter codebase.

---

## File structure / responsibilities

### Existing files to modify
- `src/hermes_max_adapter/models/max_updates.py` — заменить плоскую модель на typed inbound envelope/payload model с backward-compatible свойствами
- `src/hermes_max_adapter/updates.py` — нормализация raw payload в canonical inbound event
- `src/hermes_max_adapter/renderer.py` — canonical outbound message rendering + compatibility wrapper for text
- `src/hermes_max_adapter/adapter.py` — orchestration around canonical inbound/outbound contracts
- `src/hermes_max_adapter/plugin.py` — capability metadata exposure if feasible in current registration surface
- `tests/test_updates.py` — inbound canonical model and normalization coverage
- `tests/test_renderer.py` — outbound canonical rendering coverage
- `tests/integration/test_send_pipeline.py` — adapter send pipeline compatibility and canonical send path

### New files to create
- `src/hermes_max_adapter/models/attachments.py` — attachment kinds/source kinds/ref model
- `src/hermes_max_adapter/models/actions.py` — action button kinds/models
- `src/hermes_max_adapter/models/max_messages.py` — outbound canonical message/parts/delivery models
- `src/hermes_max_adapter/models/capabilities.py` — support level/capability declarations
- `src/hermes_max_adapter/capabilities.py` — runtime capability helper
- `src/hermes_max_adapter/upload.py` — upload source abstraction scaffold
- `tests/test_capabilities.py` — capability surface tests
- `tests/test_upload.py` — upload source abstraction tests
- `docs/api/max-format-matrix.md` — capability matrix aligned with current confirmed support/degradation

---

## Task 1: Canonical attachment and action models

**Files:**
- Create: `src/hermes_max_adapter/models/attachments.py`
- Create: `src/hermes_max_adapter/models/actions.py`
- Test: `tests/test_renderer.py`
- Test: `tests/test_updates.py`

- [ ] **Step 1: Write failing tests for attachment and action enums/models expectations**

Add tests asserting:
- attachment kinds include `photo/video/document/audio/voice/sticker/animation/contact/location/unknown`
- action button kinds include `callback/link/message/open_app/clipboard/request_contact/request_location/unknown`
- attachment refs can represent remote token, URL, and local file source

- [ ] **Step 2: Run targeted tests to verify they fail for missing module/model reason**

Run: `uv run pytest -q tests/test_renderer.py tests/test_updates.py -k 'attachment or action or canonical'`
Expected: FAIL because new models do not exist yet.

- [ ] **Step 3: Implement minimal attachment and action dataclasses/enums**

Create `attachments.py` and `actions.py` with minimal dataclasses/enums required by tests.

- [ ] **Step 4: Re-run targeted tests to verify they pass**

Run: `uv run pytest -q tests/test_renderer.py tests/test_updates.py -k 'attachment or action or canonical'`
Expected: PASS

---

## Task 2: Canonical inbound event model with compatibility properties

**Files:**
- Modify: `src/hermes_max_adapter/models/max_updates.py`
- Test: `tests/test_updates.py`

- [ ] **Step 1: Write failing tests for canonical inbound envelope and compatibility accessors**

Add tests asserting:
- canonical envelope can represent `message/callback/service/unsupported`
- message payload carries `content_type/text/caption/attachments`
- compatibility properties still expose legacy `kind/chat_id/user_id/text/update_type`

- [ ] **Step 2: Run tests to verify RED**

Run: `uv run pytest -q tests/test_updates.py -k 'canonical or compatibility'`
Expected: FAIL for missing fields/classes/properties.

- [ ] **Step 3: Implement typed inbound dataclasses with compatibility wrappers**

Keep existing legacy tests working while adding richer typed objects.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `uv run pytest -q tests/test_updates.py -k 'canonical or compatibility or normalize'`
Expected: PASS

---

## Task 3: Expand update normalization to canonical message/callback/service handling

**Files:**
- Modify: `src/hermes_max_adapter/updates.py`
- Test: `tests/test_updates.py`

- [ ] **Step 1: Write failing normalization tests for callback, service, unknown, and attachment-bearing messages**

Add tests for:
- `message_created` text payload → canonical message envelope
- live `eventType=messageCreated` with attachment-ish metadata → content classification
- `message_callback`/callback-shaped payload → canonical callback envelope
- unknown vendor type → `unsupported`
- bot/service event → `service`

- [ ] **Step 2: Run tests to verify RED**

Run: `uv run pytest -q tests/test_updates.py`
Expected: FAIL specifically on new normalization expectations.

- [ ] **Step 3: Implement minimal normalizer logic to pass without overclaiming unknown vendor facts**

Use generic extraction and safe fallbacks.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `uv run pytest -q tests/test_updates.py`
Expected: PASS

---

## Task 4: Canonical outbound message and compatibility text renderer

**Files:**
- Create: `src/hermes_max_adapter/models/max_messages.py`
- Modify: `src/hermes_max_adapter/renderer.py`
- Test: `tests/test_renderer.py`

- [ ] **Step 1: Write failing tests for canonical outbound text, attachment, and button rendering**

Add tests for:
- text-only canonical outbound message renders to `[{"text": ...}]`
- long text canonical part chunks correctly
- text + callback button renders inline keyboard attachment structure
- attachment part with caption renders attachment payload placeholder shape
- compatibility `render_outbound_payload("hello")` still works

- [ ] **Step 2: Run tests to verify RED**

Run: `uv run pytest -q tests/test_renderer.py`
Expected: FAIL on missing outbound canonical classes/renderers.

- [ ] **Step 3: Implement minimal canonical outbound models and renderer**

Keep text compatibility wrapper intact.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `uv run pytest -q tests/test_renderer.py`
Expected: PASS

---

## Task 5: Adapter orchestration over canonical contracts

**Files:**
- Modify: `src/hermes_max_adapter/adapter.py`
- Test: `tests/integration/test_send_pipeline.py`
- Test: `tests/test_updates.py`

- [ ] **Step 1: Write failing tests for canonical send path and callback-aware dedupe behavior**

Add tests asserting:
- adapter can send canonical outbound message while old `send_text_sync` remains working
- live callback/message events generate stable dedupe keys
- process_update returns canonical event envelope objects while legacy assertions still pass

- [ ] **Step 2: Run tests to verify RED**

Run: `uv run pytest -q tests/integration/test_send_pipeline.py tests/test_updates.py -k 'canonical or callback or dedupe'`
Expected: FAIL on missing adapter support.

- [ ] **Step 3: Implement minimal adapter changes**

Add:
- canonical send method internally
- compatibility wrapper for `send_text_sync`
- broader dedupe-key resolution for message/callback/service envelopes

- [ ] **Step 4: Run tests to verify GREEN**

Run: `uv run pytest -q tests/integration/test_send_pipeline.py tests/test_updates.py`
Expected: PASS

---

## Task 6: Capability surface and degradation declarations

**Files:**
- Create: `src/hermes_max_adapter/models/capabilities.py`
- Create: `src/hermes_max_adapter/capabilities.py`
- Create: `tests/test_capabilities.py`
- Create: `docs/api/max-format-matrix.md`
- Modify: `src/hermes_max_adapter/plugin.py`

- [ ] **Step 1: Write failing tests for support-level/capability snapshot**

Add tests asserting:
- support levels include `full/degraded/unsupported/unknown`
- capability snapshot declares current known support honestly
- text outbound is `full`
- callback answer remains `unknown` or `degraded`
- unsupported media types are not mislabeled `full`

- [ ] **Step 2: Run tests to verify RED**

Run: `uv run pytest -q tests/test_capabilities.py`
Expected: FAIL because capability models/helpers do not exist.

- [ ] **Step 3: Implement capability models/helpers and plugin metadata exposure where applicable**

Also write `docs/api/max-format-matrix.md` aligned with real current support.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `uv run pytest -q tests/test_capabilities.py`
Expected: PASS

---

## Task 7: Upload source abstraction scaffold

**Files:**
- Create: `src/hermes_max_adapter/upload.py`
- Create: `tests/test_upload.py`

- [ ] **Step 1: Write failing tests for upload source normalization**

Add tests asserting support for:
- vendor token ref
- local file path ref
- external URL ref
- explicit failure on unknown source kind

- [ ] **Step 2: Run tests to verify RED**

Run: `uv run pytest -q tests/test_upload.py`
Expected: FAIL because module is missing.

- [ ] **Step 3: Implement minimal upload source abstraction scaffold**

Do not fake vendor upload yet; only normalize/validate source types and return typed result scaffold.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `uv run pytest -q tests/test_upload.py`
Expected: PASS

---

## Task 8: Full verification

**Files:**
- Verify only

- [ ] **Step 1: Run focused regression suite**

Run: `uv run pytest -q tests/test_updates.py tests/test_renderer.py tests/test_capabilities.py tests/test_upload.py tests/integration/test_send_pipeline.py`
Expected: PASS

- [ ] **Step 2: Run full project suite**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 3: Review diff for honesty and no text-only regressions**

Check that:
- legacy text path still passes
- no unsupported capability is mislabeled
- no raw TODO/debug junk remains

---

## Notes
- This plan intentionally establishes the production-shaped domain model first.
- It does **not** claim fully implemented vendor media upload/send for every type yet; instead it lands the architecture, capability surface, and honest degradation behavior needed for a real production adapter.
- Any newly discovered live vendor payload shape must be added as a regression test before changing normalization logic.
