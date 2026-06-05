# Hermes MAX Adapter — Production Specification

**Date:** 2026-06-03  
**Status:** Draft for implementation  
**Project:** `hermes-max-adapter`  
**Goal:** Построить production-grade интеграцию канала MAX Bot API с Hermes Agent так, чтобы Hermes работал в MAX как полноценный conversational bot channel, а не временный хак.

---

## 1. Executive summary

Рекомендуемый путь — **native Hermes platform adapter через plugin system**, а не внешний bridge как основной боевой режим.

Почему:
- у Hermes это **официально рекомендованный путь** для third-party/community platform integrations;
- Hermes уже моделирует каналы через `BasePlatformAdapter`, per-chat session store, home-channel delivery, routing, authorization hooks и cron-delivery;
- MAX для production требует **Webhook-only**, HTTPS, port 443, retry/backoff и auto-unsubscribe rules — это лучше закрывать внутри адаптера как first-class channel integration, а не разносить на несколько полу-связанных сервисов;
- bridge остаётся полезным как fallback/MVP path, но для «не стыдно показать» лучше строить **нативный adapter plugin** с чётким operational hardening.

**Итоговая архитектурная рекомендация:**
1. Основной продукт: `MAX Hermes Gateway Plugin`.
2. Внутри него: inbound webhook server + outbound MAX API client + session mapping + callback handling + delivery safeguards.
3. Отдельно предусмотреть dev-mode long polling только для локальной отладки, **но не считать его production path**.

---

## 2. Product scope

### In scope
- Приём входящих MAX updates и доставка их в Hermes Gateway.
- Отправка сообщений из Hermes обратно в MAX.
- Поддержка DM и group/chat delivery там, где это возможно по MAX API.
- Webhook-first production deployment.
- Обработка callback/inlined actions, если MAX API их даёт через update types.
- Безопасность webhook ingress.
- Идемпотентность и защита от дублей.
- Retry-aware processing.
- Chunking длинных ответов Hermes под лимиты MAX.
- Наблюдаемость: health, logs, counters, failure diagnostics.
- Документация и config для развёртывания.

### Out of scope for first release
- Полная parity со всеми Telegram-specific UX-фичами Hermes.
- Rich media matrix всех возможных типов вложений без подтверждённой официальной схемы.
- Голосовые/видео/файловые workflows до подтверждения официальных контрактов.
- Multi-tenant control plane.
- Управление ботом через UI.

---

## 3. Confirmed facts from research

### 3.1 MAX Bot API

Подтверждено по официальным/почти официальным источникам:

- MAX Bot API поддерживает **Webhook и Long Polling**.
- Для **production** MAX рекомендует **Webhook only**.
- Long Polling официально не подходит для production из-за ограничений по скорости и хранению событий.
- Нельзя использовать Webhook и Long Polling одновременно.
- Webhook подписка создаётся через **`POST /subscriptions`**.
- Список текущих webhook subscriptions — **`GET /subscriptions`**.
- После подписки MAX шлёт **HTTPS POST** с объектом `Update`.
- Webhook endpoint должен быть доступен только по **HTTPS** на **порт 443**.
- Self-signed сертификаты не поддерживаются.
- Нужен сертификат от доверенного CA, валидный hostname и полная certificate chain.
- Endpoint должен ответить **HTTP 200 за 30 секунд**.
- Любой другой код или timeout = delivery failure.
- MAX делает до **10 retry** с exponential backoff: `60s`, `150s`, `375s`, далее ×2.5.
- Если 8 часов нет успешного ответа, MAX автоматически **отписывает бот от webhook**.
- В webhook можно передать `secret`; если он задан, MAX присылает его в **`X-Max-Bot-Api-Secret`**.
- Официально рекомендуется валидировать этот header.
- API auth token передаётся через **`Authorization`** header.
- Для стабильной работы ботов MAX рекомендует держать трафик к `platform-api.max.ru` в пределах **30 rps**.
- Официальный send-message endpoint: **`POST /messages`**.
- В примерах и смежных источниках фигурируют update/event names: `message_created`, `message_callback`, `bot_started`.

### 3.2 Hermes Agent

Подтверждено по официальной документации Hermes:

- Hermes Gateway строится вокруг **platform adapters**.
- Для third-party/community integrations официальный рекомендуемый путь — **plugin-based platform adapter**.
- Плагин может регистрировать платформу через `ctx.register_platform(...)`.
- Адаптер наследуется от **`BasePlatformAdapter`**.
- Типовые методы: `connect`, `disconnect`, `send`, `get_chat_info`.
- Доступны registration hooks/fields для production use:
  - `required_env`
  - `validate_config`
  - `env_enablement_fn`
  - `cron_deliver_env_var`
  - `allowed_users_env`
  - `allow_all_env`
  - `max_message_length`
  - `platform_hint`
  - `emoji`
- Hermes platform path лучше совпадает с:
  - session store per chat
  - delivery routing
  - home channel
  - cron delivery
  - authorization behavior
- API Server у Hermes — официальный surface, но он **stateless** по chat completions и хуже подходит как основной путь для нативного messaging channel.

---

## 4. Assumptions and open questions

Ниже вещи, которые нельзя фиксировать как факты до следующего research/implementation pass:

### Likely, but not fully confirmed
- Полная официальная схема `POST /messages` body/response.
- Полный официальный список MAX update types.
- Официальная attachment/media schema.
- Подробные ограничения на edit/delete сообщений.
- Полная схема callback answer API.
- Реальные правила thread/reply semantics в MAX.
- Все лимиты кроме 30 rps global guidance.

### Design implication
Архитектуру надо строить так, чтобы:
- неизвестные media/event types не ломали канал;
- unsupported features деградировали безопасно;
- adapter contract не предполагал лишнего про MAX, чего мы не подтвердили.

---

## 5. Architecture decision

## Decision
**Строим Hermes MAX integration как plugin-based native platform adapter.**

### Rejected alternative: API bridge as primary architecture
Почему не как основной путь:
- bridge переносит session semantics наружу;
- сложнее сохранить natural Hermes channel behavior;
- inbound/outbound auth, dedupe, retries и delivery policy оказываются размазаны по двум системам;
- для «боевого» качества это повышает operational complexity, а не снижает её.

### Accepted compromise
Для локальной разработки допускается:
- dev fallback на long polling;
- тестовый thin bridge/mock harness для black-box verification.

Но public story и production spec должны опираться на **native plugin adapter**.

---

## 6. Target architecture

### 6.1 High-level components

1. **MAX Platform Plugin**
   - Hermes plugin entrypoint
   - register platform/config/tooling metadata

2. **MAX Adapter**
   - `BasePlatformAdapter` implementation
   - connect/disconnect/send/get_chat_info
   - bootstraps inbound transport and outbound client

3. **Inbound Webhook Server**
   - принимает HTTPS POST updates от MAX
   - валидирует secret header
   - быстро подтверждает `200 OK`
   - enqueue + async process

4. **Outbound MAX Client**
   - HTTP client для MAX API
   - auth header
   - retry policy for transient failures
   - rate limiting
   - observability around requests

5. **Update Normalizer**
   - превращает `Update` → Hermes `MessageEvent` / equivalent adapter input
   - классифицирует unknown/unsupported events

6. **Session Mapper**
   - MAX user/chat identifiers → Hermes chat/session identifiers
   - DM/group separation
   - reply metadata mapping

7. **Delivery Renderer**
   - Hermes outbound content → MAX message payload
   - chunking under message size limit
   - formatting downgrade if unsupported
   - inline keyboard mapping when supported

8. **Dedupe / Idempotency Layer**
   - предотвращает double-processing webhook retries
   - хранит delivery keys / processed event keys

9. **Operational Safety Layer**
   - webhook re-subscribe watchdog
   - health endpoints / status
   - structured logs / metrics

---

## 7. File and module plan

Рекомендуемая структура проекта:

```text
hermes-max-adapter/
  AGENTS.md
  CLAUDE.md -> AGENTS.md
  README.md
  pyproject.toml
  src/hermes_max_adapter/
    __init__.py
    plugin.py
    adapter.py
    config.py
    client.py
    webhook_server.py
    updates.py
    mapping.py
    renderer.py
    rate_limit.py
    dedupe.py
    models/
      __init__.py
      max_updates.py
      max_messages.py
    observability.py
  tests/
    test_updates.py
    test_renderer.py
    test_dedupe.py
    test_webhook_security.py
    test_send_chunking.py
    integration/
      test_webhook_flow.py
      test_callback_flow.py
      test_delivery_failures.py
  docs/
    specs/
      hermes-max-adapter-spec.md
    api/
      max-bot-api-notes.md
    research/
      scout-max-hermes-research.md
      source-notes.md
    superpowers/plans/
      2026-06-03-hermes-max-adapter.md
```

---

## 8. Functional requirements

### 8.1 Inbound events
- Adapter MUST support production ingress via **Webhook**.
- Adapter MAY support long polling only behind explicit dev config.
- Inbound handler MUST validate `X-Max-Bot-Api-Secret` if secret configured.
- Inbound handler MUST return `200 OK` quickly and offload processing asynchronously.
- Inbound handler MUST detect and ignore duplicate deliveries.
- Inbound handler MUST log unknown event types without crashing.

### 8.2 Outbound messaging
- Adapter MUST send text replies through official MAX API endpoint(s).
- Adapter MUST respect MAX rate limits with local throttling/backoff.
- Adapter MUST chunk long Hermes responses when message exceeds platform limit.
- Adapter SHOULD preserve reply-to semantics where official API supports it.
- Adapter SHOULD degrade unsupported formatting safely to plain text.

### 8.3 Session behavior
- DM and group chat identities MUST be mapped deterministically.
- Session key strategy MUST be explicit and test-covered.
- Adapter MUST avoid cross-chat session bleed.
- If Hermes supports per-user grouping within group chats, this policy MUST be configurable.

### 8.4 Reliability
- Duplicate webhook deliveries MUST be idempotent.
- Transient MAX API failures SHOULD retry with bounded backoff.
- Permanent failures MUST be surfaced in logs/metrics.
- Adapter MUST expose readiness/health signals.
- System SHOULD detect webhook unsubscribe/drift and support re-subscription flow.

### 8.5 Security
- Secrets MUST come only from env/config, never from source.
- Webhook secret validation MUST be constant-time compare.
- Request payloads MUST be size-bounded.
- Logs MUST redact secrets/tokens.
- Optional allowlist / allowed-users semantics SHOULD integrate with Hermes platform registration.

### 8.6 Observability
- Structured logs for inbound update, dedupe decision, outbound send, MAX error, retry, callback processing.
- Metrics at minimum:
  - inbound_updates_total
  - duplicate_updates_total
  - outbound_messages_total
  - outbound_failures_total
  - webhook_validation_failures_total
  - unknown_update_types_total
  - max_rate_limit_hits_total

---

## 9. Non-functional requirements

- **Production-first**: webhook-only mainline path.
- **Fast ACK**: webhook requests acknowledged well under MAX 30s budget.
- **Graceful degradation**: unsupported event/media types do not kill adapter.
- **Deterministic behavior**: idempotency and session mapping reproducible.
- **Hermes-native ergonomics**: channel should feel like a first-class Hermes platform.
- **Low surprise ops**: deploy, rotate secret, re-subscribe, inspect health, replay local tests.

---

## 10. Security design

### Threats
- Spoofed webhook calls.
- Replay of old webhook requests.
- Duplicate deliveries causing double replies.
- Bot token leakage.
- Log leakage.
- Outbound spam loop from internal bug.

### Controls
- Validate `X-Max-Bot-Api-Secret`.
- Optional replay window / event-id dedupe store.
- Idempotency key persisted with TTL.
- Secret/token via env only.
- Redaction in logs.
- Outbound local rate limiter.
- Safe defaults: webhook mode by default, long polling opt-in only.

---

## 11. Reliability and operations

### Deployment model
Production deployment should assume:
- public HTTPS ingress on port 443;
- reverse proxy / ingress with trusted cert;
- app worker behind it;
- persistent state for dedupe (Redis preferred, or local durable fallback for single-node dev);
- separate health endpoint or gateway status integration.

### Recommended runtime behavior
- ACK webhook immediately after validation and queueing.
- Never block webhook request on LLM completion.
- Outbound send runs in async worker path.
- Re-subscribe command/script available for ops.
- Startup checks:
  - token present
  - webhook URL configured
  - secret configured
  - TLS expectation documented

### Failure policy
- MAX 4xx from bad payload: log + fail permanently.
- MAX 429/5xx/network: bounded retries with jitter.
- Unknown update schema: record sample payload safely, skip processing.

---

## 12. Testing strategy

### Unit tests
- update normalization
- event type routing
- secret validation
- dedupe key generation
- session mapping
- outbound payload rendering
- chunking logic
- rate limiter behavior

### Integration tests
- webhook request → queued processing → Hermes event path
- callback/button flow
- duplicate delivery replay
- outbound MAX failure and retry behavior
- unsupported event handling
- webhook invalid secret rejection

### Acceptance tests
- DM conversation roundtrip
- group chat roundtrip
- long Hermes answer split into multiple MAX messages
- callback action path if supported
- restart/reconnect without duplicate processing

### Verification bar
Нельзя говорить “готово”, пока не пройдены:
- unit suite
- integration suite
- one black-box local end-to-end simulation
- manual verification checklist in `docs/verify/`

---

## 13. Implementation phases

### Phase 0 — Contract capture
- Собрать в проекте source notes и ссылки.
- Зафиксировать confirmed vs open questions.
- Описать config/env surface.

### Phase 1 — Skeleton plugin
- `plugin.py`
- `adapter.py`
- config loading
- registration metadata
- base send/connect/disconnect contract

### Phase 2 — Inbound webhook path
- webhook server
- secret validation
- quick ACK
- queue/async processing
- dedupe store

### Phase 3 — Outbound delivery
- MAX client
- send message path
- chunking
- formatting downgrade
- rate limiting/backoff

### Phase 4 — Session/callback semantics
- inbound mapping
- reply metadata
- callback/update routing
- group vs DM handling

### Phase 5 — Hardening
- metrics/logging
- watchdog/re-subscribe support
- failure taxonomy
- stronger test matrix
- docs/README/deploy guide

---

## 14. Recommended config surface

Пример env-переменных:

```text
MAX_BOT_TOKEN=
MAX_WEBHOOK_SECRET=
MAX_WEBHOOK_URL=
MAX_HOME_CHANNEL=
MAX_ALLOWED_USERS=
MAX_ALLOW_ALL_USERS=false
MAX_ENABLE_LONG_POLLING=false
MAX_API_BASE_URL=https://platform-api.max.ru
MAX_REQUEST_TIMEOUT_SECONDS=15
MAX_OUTBOUND_RPS=20
MAX_DEDUPE_BACKEND=redis
MAX_REDIS_URL=
```

### Registration expectations in Hermes
- `required_env`: token / webhook essentials
- `allowed_users_env`: support if meaningful for MAX user identities
- `allow_all_env`: explicit override
- `cron_deliver_env_var`: home-channel support
- `max_message_length`: set once official text limit fully confirmed in implementation pass
- `platform_hint`: short prompt hint about MAX formatting constraints

---

## 15. Documentation artifacts to produce

Before coding completes, repo must contain:
- `README.md` — what it is, quickstart, deploy model
- `docs/specs/hermes-max-adapter-spec.md` — this spec
- `docs/api/max-bot-api-notes.md` — extracted API facts and unresolved areas
- `docs/research/scout-max-hermes-research.md` — scout report
- `docs/research/source-notes.md` — raw source list with confidence
- `docs/superpowers/plans/2026-06-03-hermes-max-adapter.md` — execution plan

---

## 16. Open questions to resolve during implementation discovery

1. Exact official request/response schema of `POST /messages`.
2. Exact MAX max text length and rich formatting guarantees.
3. Full official list of update types and callback payload structures.
4. Whether edit/delete operations are needed in v1 and what their hard limits are.
5. Whether MAX supports message reply threading in a way Hermes can map natively.
6. Best dedupe key source from real webhook payload.
7. Whether attachments/media can be included safely in v1 or should be feature-flagged.

---

## 17. Final recommendation

Если делаем «боевой режим, который не стыдно показать», надо сразу строить **plugin-based native Hermes adapter for MAX**, с таким принципом:

- production path = **Webhook**;
- adapter path = **Hermes native platform plugin**;
- security = **secret validation + dedupe + safe logging**;
- reliability = **fast ACK + async processing + retry-aware outbound**;
- UX = **session-safe conversational channel**;
- rollout = **feature-complete text+callbacks first, richer media later under confirmed contracts**.

Это самый ровный и наименее стыдный путь.
