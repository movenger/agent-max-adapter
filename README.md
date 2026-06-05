# Hermes MAX Adapter

Production-ready MAX Bot API adapter plugin for Hermes Agent.

## What is already proven

Live-confirmed against the real MAX client/API:
- inbound webhook delivery
- outbound text
- outbound document
- outbound image/photo
- outbound video

Fresh automated verification:
- `pytest -q` → `159 passed`

## Current status

This repo is ready to show as a working Hermes/MAX adapter and is close to public-repo ready.
It is a real working plugin codebase, not a mock or toy prototype.

The remaining work is mostly repo polish and docs clarity, not core runtime bring-up.

## Architecture overview

High-level shape:
- `plugin.py` exposes Hermes plugin registration
- `adapter.py` implements the MAX adapter runtime
- `webhook_app.py` / `webhook_server.py` handle inbound webhook ingress
- `client.py` / `transport.py` handle outbound MAX API requests
- `renderer.py` / `upload.py` map Hermes outbound content into MAX payloads
- `updates.py` / `mapping.py` normalize inbound MAX updates
- `dedupe.py` / `rate_limit.py` / `observability.py` provide runtime safety

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e . pytest
pytest -q
python scripts/setup.py
```

## Minimal local bootstrap

```bash
cp .env.example .env
python scripts/setup.py
```

## Setup wizard

Run the interactive wizard:

```bash
python scripts/setup.py
```

The wizard can:
- check environment dependencies before setup
- create or refresh `.venv`
- install Python project dependencies automatically
- detect Docker / Docker Compose / daemon access problems
- offer guided install for missing Docker or Docker Compose
- configure token-only mode or webhook-ready mode
- configure local, external, or skipped Redis
- validate webhook and Redis URLs
- write `.env`
- optionally run smoke checks after setup

## Required environment

- `MAX_BOT_TOKEN`
- `MAX_WEBHOOK_SECRET`
- `MAX_WEBHOOK_URL`

## Optional environment

- `MAX_ENABLE_LONG_POLLING`
- `MAX_MAX_RETRIES`
- `MAX_RETRY_BACKOFF_SECONDS`
- `MAX_REQUEST_TIMEOUT_SECONDS`
- `LOCAL_WEBHOOK_PORT`
- `REDIS_URL`
- `MAX_DEDUPE_TTL_SECONDS`

## Token-only mode

Token-only mode is supported for early setup before a public webhook exists.
In token-only mode you can validate outbound flow first, then move to webhook mode later.
Use the live outbound smoke script to verify real outbound delivery:
- `python scripts/live_outbound_smoke.py`

## Local Redis

This repo includes a local Redis development path for dedupe/idempotency work.

```bash
docker compose up -d redis
python scripts/redis_smoke.py
```

## Hermes integration

Plugin entrypoint is implemented in:
- `src/hermes_max_adapter/plugin.py`

It exposes:
- `build_registration()`
- `validate_config()`
- `adapter_factory`

If you want the fastest attach path, start here:
- `docs/integration/quick-attach.md`

Current plugin runtime notes:
- see `docs/specs/plugin-runtime.md`
- see `docs/integration/hermes.md`
- see `docs/integration/quick-attach.md`

## Hermes config example

Conceptually Hermes should provide a config object whose fields map like this:

```python
cfg.bot_token = os.environ["MAX_BOT_TOKEN"]
cfg.extra = {
    "token": os.environ["MAX_BOT_TOKEN"],
    "webhook_secret": os.environ.get("MAX_WEBHOOK_SECRET", ""),
    "webhook_url": os.environ.get("MAX_WEBHOOK_URL"),
    "enable_long_polling": False,
}
```

The plugin registration then builds `MaxAdapter` from that config via `adapter_factory`.

## Local/dev tools

- setup wizard: `python scripts/setup.py`
- local demo: `python examples/local_demo.py`
- local webhook server: `python examples/local_webhook_server.py`
- outbound live smoke: `python scripts/live_outbound_smoke.py`
- webhook/subscription smoke: `python scripts/live_smoke.py`
- redis smoke: `python scripts/redis_smoke.py`
- watchdog helper: `python scripts/watchdog.py`

## Subscription handling

This adapter includes subscription reconcile foundation.
Recommended operational pattern:
- inspect current remote subscriptions on startup
- re-subscribe if remote state drifts from local config
- run a watchdog to detect webhook drift or silent unsubscribe

## Deployment notes

Production guidance:
- HTTPS only
- webhook endpoint on public 443 via reverse proxy
- trusted TLS certificate
- secret validation on webhook ingress
- `docker compose` can be used locally for Redis-backed development

See:
- `docs/specs/deployment.md`

## Capability truth

For the honest verified state, see:
- `docs/max-media-truth.md`
- `docs/api/max-format-matrix.md`

## Repo scope

This repo contains:
- Hermes plugin registration
- MAX adapter runtime
- webhook ingress handling
- outbound client / upload flow
- normalization / rendering / retry / dedupe
- setup scripts and smoke scripts
- tests and deployment notes

## Publication checklist

Before publishing:
- ensure `.env`, `.venv`, `tmp/`, and caches are not committed
- run `pytest -q`
- re-read `README.md`
- re-read `docs/integration/hermes.md`
- verify capability/status docs still match live truth

## Known boundary

This repo is runtime-shaped for Hermes, but the plugin has not yet been proven inside a full public Hermes gateway distribution as an end-user install package. The adapter code itself is tested and the MAX flows above are live-confirmed.
