# Scout / external research digest

**Date:** 2026-06-03

## Hermes Agent findings

Confirmed from official Hermes docs:
- Hermes Gateway integrates channels via **platform adapters**.
- For third-party/community channels, the **recommended path is a plugin-based adapter**.
- Adapters subclass `BasePlatformAdapter`.
- Standard lifecycle includes `connect`, `disconnect`, `send`, `get_chat_info`.
- `ctx.register_platform(...)` supports production-use fields like:
  - `required_env`
  - `validate_config`
  - `env_enablement_fn`
  - `cron_deliver_env_var`
  - `allowed_users_env`
  - `allow_all_env`
  - `max_message_length`
  - `platform_hint`
  - `emoji`
- Hermes API Server exists, but is better suited as a backend/API surface than as the primary implementation strategy for a first-class messaging channel.
- Hermes Webhooks are useful for event automation, not ideal as the main primitive for a full conversational channel.

## MAX findings

Confirmed/near-confirmed:
- Production path should use **Webhook**, not Long Polling.
- Webhook requirements are strict: HTTPS, port 443, trusted certs, full chain, fast 200 response.
- Delivery retries and auto-unsubscribe behavior make async ACK + queue processing a must.
- At least these update names are visible in official/near-official material:
  - `message_created`
  - `message_callback`
  - `bot_started`
- Official send-message endpoint is `POST /messages`.
- Official rate guidance found: `30 rps`.

## Production recommendation

Build **native Hermes platform plugin for MAX** as the public/production path.

Why:
- Best alignment with Hermes session and routing model.
- Better operational coherence than a split bridge.
- Easier to expose as a real Hermes channel rather than a hidden middleware workaround.
- More future-proof if the adapter later graduates into wider community use.

## Risks / unknowns to handle explicitly
- Full MAX message schema not yet locked.
- Full event taxonomy not yet locked.
- Media support should be feature-gated until official contracts are verified.
- Reply/thread semantics may require careful fallback behavior.
