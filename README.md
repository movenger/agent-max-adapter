# Hermes MAX Adapter

Open-source MAX connector package for agent runtimes.

What a user should be able to do:
- clone the repo
- install dependencies
- configure bot token / webhook URL / secret
- attach to their runtime
- run smoke checks
- start using MAX without custom project surgery

## Current readiness

Closest to ready:
- Hermes

Partially ready:
- OpenClaw native target exists and tests pass in upstream repo
- GoClaw native target exists, but wider upstream attach proof is blocked by unrelated build debt in GoClaw

## What is already proven

Live-confirmed against the real MAX client/API:
- inbound webhook delivery
- outbound text
- outbound document
- outbound image/photo
- outbound video

Fresh automated verification:
- `pytest -q` → `180 passed`

Focused upstream proof:
- OpenClaw native MAX extension tests pass in `~/workspaces/openclaw`
- GoClaw native MAX package test passes in `~/workspaces/goclaw/internal/channels/max`

## Architecture overview

High-level shape:
- `plugin.py` exposes Hermes plugin registration
- `adapter.py` implements the shared MAX adapter core
- `webhook_app.py` / `webhook_server.py` handle inbound webhook ingress
- `client.py` / `transport.py` handle outbound MAX API requests
- `renderer.py` / `upload.py` map outbound content into MAX payloads
- `updates.py` / `mapping.py` normalize inbound MAX updates
- `dedupe.py` / `rate_limit.py` / `observability.py` provide runtime safety

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e . pytest
action='cp .env.example .env'
python scripts/setup.py
pytest -q
```

`examples/local_demo.py` is available for a minimal local demo harness.

## Setup wizard

`scripts/setup.py` is the setup wizard.
It can:
- validate the local environment
- check Docker / docker compose availability
- write `.env`
- keep a token-only flow for early bring-up
- prepare webhook-ready mode

## Minimum config

Required values:
- `MAX_BOT_TOKEN`
- `MAX_WEBHOOK_SECRET`
- `MAX_WEBHOOK_URL`

Optional values:
- `REDIS_URL`
- `MAX_ENABLE_LONG_POLLING`
- retry / timeout settings

## Token-only mode

Token-only mode is supported for early outbound verification before a public webhook is ready.
Use the live outbound smoke helper first:
- `python scripts/live_outbound_smoke.py`

## Local Redis / dedupe

For local Redis-backed dedupe work:

```bash
docker compose up -d redis
python scripts/redis_smoke.py
```

Use `REDIS_URL` to point at your Redis instance.

## Included local verification helpers

These scripts auto-load repo-local `.env`:
- `python scripts/live_smoke.py`
- `python scripts/live_outbound_smoke.py`
- `python scripts/watchdog.py`
- `python scripts/redis_smoke.py`
- `python examples/local_webhook_server.py`

## Subscription handling

The repo includes subscription reconcile helpers.
Operationally you should verify:
- subscription exists
- webhook URL matches config
- watchdog can detect drift

## Runtime attach docs

- Hermes: `docs/integration/hermes.md`
- OpenClaw: `docs/integration/openclaw-attach.md`
- GoClaw: `docs/integration/goclaw-attach.md`
- Multi-runtime status: `docs/integration/multi-runtime.md`
- Quick attach: `docs/integration/quick-attach.md`

## Honest boundary

Ready now:
- public package bootstrap
- repo-local setup flow
- Hermes integration path
- OpenClaw native target location + passing local upstream tests
- GoClaw native target location + passing focused package proof

Not yet fully proven for strangers:
- full clean-room OpenClaw attach outside current upstream workspace
- full GoClaw upstream attach until unrelated `internal/channels/manager.go` build debt is fixed

## Capability truth

For the verified state, see:
- `docs/max-media-truth.md`
- `docs/openclaw-goclaw-upstream-truth.md`
