# Hermes MAX Adapter — Full Production Message Contract Design

**Date:** 2026-06-03  
**Status:** Draft for review  
**Project:** `hermes-max-adapter`  
**Goal:** Спроектировать боевой MAX ↔ Hermes adapter как полноценный production-grade messaging channel с расширяемой моделью событий, сообщений, медиа, интерактивности, деградации, observability и capability-declaration — без text-only архитектуры и без хрупких ad-hoc веток.

---

## 1. Executive summary

Текущая репа даёт **text-first foundation**, но она недостаточна для боевого адаптера.  
Проблема не в отсутствии ещё пары форматов, а в том, что текущая внутренняя модель слишком бедная:

- `NormalizedEvent` содержит только `kind/chat_id/user_id/text/update_type`
- `renderer.py` умеет только текст
- `adapter.py` оркестрирует только text send path
- media/button/callback/service semantics сейчас не являются first-class contract

Для production-grade варианта нужен не набор точечных фич, а **полная внутренняя модель канала**:

- typed inbound events
- typed outbound messages
- attachment/media abstraction
- interaction/callback abstraction
- service/system event abstraction
- capability surface
- safe degradation policy
- upload/send lifecycle model
- strict testing matrix

**Архитектурное решение:**
строим MAX integration как **plugin-based native Hermes platform adapter** с **typed envelope + typed content objects**, совместимыми с последующей эволюцией в registry/handler architecture, но без преждевременного переусложнения.

---

## 2. Design constraints

### 2.1 Product constraints
- Нужен **боевой**, а не быстрый вариант.
- Нельзя строить архитектуру вокруг text-only happy path.
- Нужно проектировать так, чтобы новые MAX payload types добавлялись без развала модели.
- Unknown / future vendor changes не должны валить адаптер.

### 2.2 Repository constraints
Из `AGENTS.md`:
- docs/spec/contracts должны быть записаны до серьёзного product-кода;
- uncertain vendor facts должны быть отмечены как assumptions/open questions;
- нельзя выдавать предположения за контракт.

### 2.3 Vendor constraints (confirmed)
Подтверждено research-материалами и уже отражено в `docs/api/max-bot-api-notes.md`:
- production path для MAX — **Webhook**, не Long Polling;
- webhook requires **HTTPS**, **port 443**, trusted CA certs;
- при наличии subscription secret MAX присылает `X-Max-Bot-Api-Secret`;
- endpoint должен вернуть **HTTP 200** быстро, иначе delivery считается failed;
- MAX retry’ит delivery и может auto-unsubscribe после длительных failure;
- outbound send endpoint: `POST /messages`;
- в экосистеме видны event names: `message_created`, `message_callback`, `bot_started`.

### 2.4 Vendor uncertainty constraints
Не подтверждено полностью:
- полный shape `Update`
- полная media attachment schema
- полный callback-answer schema
- service/system event taxonomy
- media/upload limits and exact payload forms

**Следствие:** модель должна быть production-grade, но при этом не должна кодировать неподтверждённые vendor assumptions как жёсткие факты.

---

## 3. Architecture options considered

### Option A — Expand the current flat model
Добавить в текущий `NormalizedEvent` поля под media/callback/buttons/service.

**Rejected.**  
Причины:
- быстро превратится в giant nullable struct;
- boundaries between inbound/outbound/message/callback/service будут смешаны;
- тесты станут хрупкими;
- эволюция новых типов будет дорогой.

### Option B — Typed envelope + typed content objects
Ввести:
- общий event envelope
- typed message/callback/service payloads
- typed attachments/actions/outbound parts
- отдельные inbound/outbound contracts
- explicit degradation and capability policy

**Accepted.**  
Причины:
- production-shape without premature overengineering;
- хорошо тестируется;
- расширяется без массовой переделки;
- позволяет безопасно жить с vendor uncertainty.

### Option C — Full registry-per-type architecture from day one
Отдельный handler/codec/renderer registry на каждый формат.

**Not chosen as initial implementation shape.**  
Причины:
- на текущей кодовой базе это риск слишком раннего enterprise-framework подхода;
- полезно как эволюционный следующий шаг, но не как первый боевой рефакторинг.

---

## 4. Target architecture

### 4.1 Architectural principle
Внутренний контракт строится не вокруг конкретного MAX JSON, а вокруг **канонической модели канала**.  
MAX raw payload → inbound normalization → canonical objects → Hermes/runtime handling → outbound canonical message → MAX rendering/upload/send.

### 4.2 Layer map

1. **Plugin registration layer**
   - Hermes plugin entrypoint
   - platform metadata and capability exposure

2. **Inbound transport layer**
   - webhook ingress
   - secret validation
   - fast ACK and async dispatch
   - raw event capture / logging

3. **Inbound normalization layer**
   - raw MAX update → canonical `InboundEvent`
   - message/callback/service discrimination
   - attachment extraction
   - unknown/future type capture

4. **Adapter orchestration layer**
   - dedupe
   - session mapping
   - runtime delivery into Hermes
   - observability increments

5. **Outbound canonical composition layer**
   - Hermes content → canonical `OutboundMessage`
   - compound message validation
   - capability checks

6. **Outbound render/upload layer**
   - canonical parts → MAX payload(s)
   - upload resolution for local/url/remote refs
   - button rendering
   - fallback/decomposition rules

7. **Delivery transport layer**
   - MAX API client
   - retry classification
   - rate limiting
   - typed send results

8. **Operational safety layer**
   - counters/logs
   - degraded feature reporting
   - health/capability snapshot
   - webhook drift/watchdog support

---

## 5. Canonical domain model

## 5.1 Core rule
Inbound and outbound are **not the same object**.  
They share domain concepts, but they have different responsibilities and must remain separate contracts.

## 5.2 Inbound event model

### `InboundEventEnvelope`
Purpose: top-level normalized event independent of MAX raw shape.

Required semantics:
- `event_id: str | None`
- `event_type: InboundEventType`
- `vendor_event_name: str`
- `occurred_at: str | None`
- `chat_id: str | None`
- `user_id: str | None`
- `message_id: str | None`
- `delivery_key: str`
- `payload: InboundPayload`
- `raw: dict`
- `degradation_flags: list[str]`

### `InboundEventType`
Stable enum surface:
- `message`
- `callback`
- `service`
- `unsupported`

### `InboundPayload`
Discriminated union:
- `InboundMessage`
- `InboundCallback`
- `InboundServiceEvent`
- `UnsupportedInboundPayload`

## 5.3 Inbound message model

### `InboundMessage`
Required semantics:
- `content_type: MessageContentType`
- `text: str | None`
- `caption: str | None`
- `attachments: list[AttachmentRef]`
- `entities: list[TextEntity]`
- `reply_to_message_id: str | None`
- `thread_id: str | None`
- `sender_display_name: str | None`
- `chat_title: str | None`
- `album_id: str | None`
- `metadata: dict[str, Any]`

### `MessageContentType`
Production enum surface:
- `text`
- `photo`
- `video`
- `document`
- `audio`
- `voice`
- `sticker`
- `animation`
- `contact`
- `location`
- `media_group`
- `mixed`
- `unknown`

## 5.4 Callback model

### `InboundCallback`
Required semantics:
- `callback_id: str | None`
- `data: str | None`
- `button_text: str | None`
- `origin_message_id: str | None`
- `origin_chat_id: str | None`
- `origin_user_id: str | None`
- `notification_supported: bool | None`
- `edit_supported: bool | None`
- `metadata: dict[str, Any]`

## 5.5 Service event model

### `InboundServiceEvent`
Purpose: preserve non-message updates without pretending they are ordinary messages.

Required semantics:
- `service_type: str`
- `summary: str | None`
- `actor_user_id: str | None`
- `target_user_id: str | None`
- `metadata: dict[str, Any]`

Notes:
- because MAX service taxonomy is not fully confirmed, `service_type` remains open string, not closed enum at first;
- runtime may choose to ignore or only log certain service events, but contract preserves them explicitly.

## 5.6 Attachment model

### `AttachmentRef`
Shared concept for inbound and outbound referencing.

Required semantics:
- `kind: AttachmentKind`
- `source: AttachmentSourceKind`
- `remote_id: str | None`
- `upload_token: str | None`
- `url: str | None`
- `local_path: str | None`
- `file_name: str | None`
- `mime_type: str | None`
- `size_bytes: int | None`
- `duration_seconds: int | None`
- `width: int | None`
- `height: int | None`
- `thumbnail: dict | None`
- `metadata: dict[str, Any]`

### `AttachmentKind`
- `photo`
- `video`
- `document`
- `audio`
- `voice`
- `sticker`
- `animation`
- `contact`
- `location`
- `unknown`

### `AttachmentSourceKind`
- `vendor_payload`
- `vendor_token`
- `external_url`
- `local_file`
- `in_memory`
- `generated`
- `unknown`

## 5.7 Text entity model

### `TextEntity`
Required semantics:
- `kind: str`
- `offset: int`
- `length: int`
- `url: str | None`
- `language: str | None`
- `metadata: dict[str, Any]`

Reason:
- formatting/entity parity with MAX is not fully confirmed;
- preserving generic entities is safer than flattening everything early.

## 5.8 Outbound message model

### `OutboundMessage`
Purpose: canonical send contract before rendering to MAX.

Required semantics:
- `target_chat_id: str | None`
- `target_user_id: str | None`
- `parts: list[OutboundPart]`
- `reply_to_message_id: str | None`
- `thread_id: str | None`
- `formatting_mode: str | None`
- `expected_delivery: DeliveryExpectation`
- `metadata: dict[str, Any]`

### `OutboundPart`
Discriminated union:
- `OutboundTextPart`
- `OutboundAttachmentPart`
- `OutboundActionRowPart`

### `OutboundTextPart`
- `text: str`
- `entities: list[TextEntity]`
- `allow_chunking: bool`

### `OutboundAttachmentPart`
- `attachment: AttachmentRef`
- `caption: str | None`
- `caption_entities: list[TextEntity]`

### `OutboundActionRowPart`
- `rows: list[list[ActionButton]]`

## 5.9 Action button model

### `ActionButton`
Required semantics:
- `kind: ActionButtonKind`
- `text: str`
- `payload: str | None`
- `url: str | None`
- `app_ref: str | None`
- `copy_text: str | None`
- `request_contact: bool`
- `request_location: bool`
- `metadata: dict[str, Any]`

### `ActionButtonKind`
- `callback`
- `link`
- `message`
- `open_app`
- `clipboard`
- `request_contact`
- `request_location`
- `unknown`

Important:
- only some kinds are known to generate callback updates;
- `clipboard` and `link` must not be modeled as callback-producing by default;
- unknown button kinds must fail closed on outbound or degrade explicitly.

## 5.10 Delivery result model

### `DeliveryOutcome`
Required semantics:
- `success: bool`
- `attempts: int`
- `message_ids: list[str]`
- `remote_status_code: int | None`
- `retryable: bool`
- `degraded: bool`
- `degradation_reasons: list[str]`
- `failures: list[DeliveryFailure]`

### `DeliveryFailure`
- `stage: DeliveryFailureStage`
- `reason: str`
- `status_code: int | None`
- `retryable: bool`
- `metadata: dict[str, Any]`

### `DeliveryFailureStage`
- `validation`
- `upload`
- `render`
- `send`
- `callback_answer`
- `unknown`

---

## 6. Capability surface

Боевой адаптер не должен прятать ограничения в коде или README.  
Он должен явно объявлять возможности.

### `AdapterCapabilities`
Required surfaces:
- inbound supported content kinds
- outbound supported content kinds
- button kinds supported outbound
- callback support status
- callback answer support status
- message edit/delete support status
- media upload source support (`local_file`, `url`, `token`, `bytes`)
- album/media-group support status
- service event preservation support status
- degradation rules advertised to runtime/logs/docs

### Support levels
Use explicit support levels, not boolean only:
- `full`
- `degraded`
- `unsupported`
- `unknown`

Example:
- `text_outbound = full`
- `photo_outbound = full`
- `animation_outbound = degraded`
- `callback_answer = unknown`
- `location_outbound = unsupported`

Reason:
production reality is rarely binary.

---

## 7. Degradation policy

## 7.1 Core rule
Unsupported or partially supported behavior must never pretend to be fully delivered.

## 7.2 Inbound degradation
If raw MAX payload contains unknown structure:
- do not crash;
- preserve raw payload inside envelope;
- classify as `unsupported` or `unknown` payload subtype;
- emit structured log + counter;
- preserve as much routing identity as safely extractable.

## 7.3 Outbound degradation
If Hermes asks to send content MAX path cannot faithfully deliver:
- reject clearly **or** decompose explicitly;
- do not silently drop attachments/buttons;
- mark delivery outcome as `degraded` when transformed;
- include degradation reasons in logs/result.

Examples:
- unsupported entity formatting → strip formatting and mark degraded
- unsupported attachment combo → split into multiple messages and mark degraded
- unsupported button kind → reject validation before send
- unknown media upload source → fail at validation, not halfway through transport

## 7.4 Unknown future vendor types
Unknown future inbound event types should map to:
- `event_type=unsupported`
- `vendor_event_name=<raw type if known>`
- `raw=<full raw payload>`

This is mandatory for forward compatibility.

---

## 8. Upload and media lifecycle

## 8.1 Principle
Media delivery is a two-stage concern:
1. resolve source
2. upload or reference
3. render send payload
4. send

It must not be entangled with plain text rendering.

## 8.2 Source types to support
Boевой design should support these canonical sources:
- pre-existing vendor token / remote attachment reference
- local file path
- external URL
- in-memory bytes/blob
- future generated artifact

## 8.3 Upload resolution contract
Introduce a dedicated resolver layer:
- validate source
- determine whether upload is necessary
- perform upload if required
- return canonical `AttachmentRef` usable by renderer

## 8.4 Failure handling
Upload failures must:
- be separated from send failures;
- be classified retryable vs non-retryable;
- carry type/source/stage metadata.

## 8.5 Video/audio metadata
Because exact MAX payload schema is not fully confirmed:
- metadata fields remain optional;
- model preserves width/height/duration/file_name/mime_type when known;
- renderer only uses fields actually required by supported send path.

---

## 9. Compound message rules

Боевой адаптер обязан уметь не только “один текст” или “одна фотка”.
Но compound behavior должно быть явным.

### Allowed canonical combinations
- text only
- text + buttons
- attachment + caption
- attachment + caption + buttons
- multiple attachments where vendor support exists
- media group / album as explicit content type when supported

### Validation rules
- compound combinations are validated before send
- invalid combinations fail early
- fallback split rules are explicit, not incidental

### Split policy examples
- long text → chunk into multiple text messages
- attachment + too-long caption → split caption safely
- unsupported mixed media group → decompose into sequential sends with degraded flag

---

## 10. Callback and interaction contract

## 10.1 Inbound callbacks
Callback-producing buttons must normalize to `InboundCallback` and receive:
- stable dedupe key
- payload extraction
- message/chat/user origin linkage
- raw payload preservation

## 10.2 Callback answering
Even though exact HTTP schema is not fully confirmed, the adapter architecture must reserve a first-class callback-answer path:
- `answer_callback(...)`
- `answer_callback_sync(...)`
- typed outcome with `callback_answer` failure stage

Until exact vendor contract is confirmed, capability should be `unknown` or `degraded`, not lied about.

## 10.3 Non-callback buttons
Buttons like `link` and `clipboard` must be modeled as non-callback by default unless confirmed otherwise.

---

## 11. Dedupe and idempotency

## 11.1 Inbound dedupe
Delivery key must not assume only `message_created` exists.
It must be derived from best-known stable identifiers by event type:
- message events: message id / mid / vendor message token
- callback events: callback id if present, otherwise composite fallback
- service events: vendor event id or timestamped composite fallback

## 11.2 Outbound idempotency
Design should allow future addition of outbound idempotency keys per send attempt, even if MAX API does not expose a native feature.

## 11.3 Retry safety
Webhook redelivery and internal retry must not duplicate side effects where avoidable.

---

## 12. Observability contract

## 12.1 Metrics
At minimum:
- inbound events total by event_type/vendor_event_name/result
- outbound sends total by content kind/result
- upload attempts by attachment kind/result
- duplicate events total by event_type
- degraded deliveries total by reason
- unsupported inbound/outbound total by kind
- callback answers total by result

## 12.2 Logging
Structured logs should include:
- event type
- vendor event name
- chat/user/message identifiers where safe
- degradation flags
- failure stage
- retry attempt
- upload source kind

## 12.3 Health surface
Health snapshot should expose:
- connection status
- webhook mode enabled
- long polling mode enabled (dev only)
- rate limiter status
- counters summary
- capability summary
- last known vendor contract mode/version if applicable

---

## 13. Security contract

### Required
- validate `X-Max-Bot-Api-Secret` if configured
- reject unauthorized webhook requests before payload processing
- do not log secrets or full sensitive headers
- validate URLs/local paths for outbound media sources
- fail closed on malformed callback/button payloads

### Deferred but planned
- stricter raw payload size limits
- replay-window hardening beyond dedupe keying
- signature/HMAC support if vendor later documents stronger auth than shared secret header

---

## 14. File/module design

Recommended target structure:

```text
src/hermes_max_adapter/
  plugin.py
  adapter.py
  config.py
  client.py
  transport.py
  webhook_app.py
  webhook_server.py
  updates.py
  renderer.py
  mapping.py
  observability.py
  rate_limit.py
  dedupe.py
  capabilities.py
  upload.py
  models/
    max_updates.py
    max_messages.py
    attachments.py
    actions.py
    capabilities.py
```

### Responsibilities
- `models/max_updates.py` — typed inbound envelope/payload classes
- `models/max_messages.py` — outbound canonical message model
- `models/attachments.py` — attachment refs and kinds
- `models/actions.py` — button/action types
- `models/capabilities.py` — support-level models and enums
- `updates.py` — raw MAX update normalization
- `renderer.py` — canonical outbound rendering and decomposition
- `upload.py` — upload resolution lifecycle
- `capabilities.py` — runtime capability declaration helpers
- `adapter.py` — orchestration only, not business-shape dumping ground

---

## 15. Testing strategy

## 15.1 Unit matrix — inbound
Must cover normalization for:
- text
- photo
- video
- document
- audio
- voice
- sticker
- animation
- contact
- location
- callback
- service event
- unknown future type
- media group / album

## 15.2 Unit matrix — outbound
Must cover rendering/validation for:
- text
- long text chunking
- text + buttons
- photo + caption
- video + caption
- document + caption
- audio
- voice
- callback buttons
- link buttons
- unsupported button kind
- unsupported compound combination
- degraded formatting strip
- upload-token passthrough
- local-file upload path
- external-url source

## 15.3 Integration tests
- webhook secret validation
- live webhook payload shapes already seen in real traffic
- adapter pipeline for each major content family
- dedupe on message events
- dedupe on callback events
- retry taxonomy unchanged by media sends
- degraded delivery reporting

## 15.4 Contract tests
- canonical model backward-compatibility expectations
- capability snapshot correctness
- failure-stage classification

## 15.5 Regression philosophy
Every newly discovered live MAX payload shape becomes a regression fixture.

---

## 16. Confirmed contracts vs assumptions

## Confirmed enough to encode now
- webhook production-first design
- `X-Max-Bot-Api-Secret` validation path
- `POST /messages` exists
- callback-style buttons exist
- inline keyboard attachment concept exists
- upload is a separate lifecycle from send
- unknown vendor details must be tolerated safely

## Assumptions that must remain soft
- exact JSON shape for all inbound media payloads
- exact callback answer endpoint/body
- full service event taxonomy
- album/media-group vendor semantics
- exact constraints for contact/location/sticker/animation support

**Design rule:** unsupported or unknown areas remain modeled, but capability-marked as `unknown/degraded/unsupported` until confirmed.

---

## 17. Migration impact on current codebase

Current code that will become insufficient:
- `NormalizedEvent` flat dataclass
- `render_outbound_payload(text)` text-only renderer
- `send_text_sync` as the de facto only outbound public path
- dedupe key logic tied mostly to message paths

Expected refactor direction:
- keep current text path working through compatibility wrappers;
- migrate internals to canonical objects;
- preserve passing text tests while expanding format matrix;
- avoid big-bang rewrite where verification disappears.

---

## 18. Implementation posture

This design intentionally chooses:
- **production-shaped foundation first**
- **full message/media/event model before feature patching**
- **capabilities and degradation as first-class concerns**
- **strict separation of confirmed facts vs assumptions**

It does **not** claim that all MAX vendor payload shapes are already known.  
It claims that the adapter architecture will be able to support a full production channel safely, honestly, and extensibly.

---

## 19. Recommended next step

Create an implementation plan that executes this design in staged but production-aligned order:
1. canonical models
2. inbound normalization expansion
3. outbound canonical renderer and upload lifecycle
4. callback/actions contract
5. capabilities + degradation + observability
6. full test matrix and regression fixtures
7. docs/runtime updates
