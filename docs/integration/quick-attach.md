# Quick Attach Guide

## What this repo is

Open-source MAX connector package.

Goal:
- clone from GitHub
- configure your bot token / webhook URL / secret
- attach to your agent runtime
- verify with the included smoke paths

## 1. Bootstrap

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e . pytest
cp .env.example .env
python scripts/setup.py
pytest -q
```

## 2. Minimum config

Set these values in `.env`:

```bash
MAX_BOT_TOKEN="..."
MAX_WEBHOOK_SECRET="dev-secret"
MAX_WEBHOOK_URL="https://your-domain.example/"
```

## 3. Hermes attach

Conceptual wiring:

```python
from hermes_max_adapter.plugin import build_registration

registration = build_registration()
adapter = registration["adapter_factory"](cfg)
```

Then verify:
- registration loads
- adapter connects
- webhook ingress works
- text send works
- document / image / video send works

See:
- `docs/integration/hermes.md`

## 4. OpenClaw attach

Current state:
- native bundled plugin package exists in upstream OpenClaw repo under `extensions/max/`
- validated locally against OpenClaw extension tests

Important boundary:
- this repo contains the proven MAX core and public attach contract
- real OpenClaw attach is runtime-native and must be exercised from the OpenClaw repo/runtime

See:
- `docs/integration/openclaw-attach.md`

## 5. GoClaw attach

Current state:
- native GoClaw MAX channel skeleton exists in upstream GoClaw repo under `internal/channels/max/`
- focused package-level proof exists
- wider `internal/channels` verification is currently blocked by pre-existing logging-format build debt in upstream `manager.go`

Important boundary:
- this repo provides the MAX core and contract model
- real GoClaw attach remains runtime-native Go work inside the GoClaw repo

See:
- `docs/integration/goclaw-attach.md`

## 6. Smoke paths in this repo

These scripts now load repo-local `.env` automatically:

```bash
python scripts/live_smoke.py
python scripts/live_outbound_smoke.py
python scripts/watchdog.py
python scripts/redis_smoke.py
python examples/local_webhook_server.py
```

## 7. Honest readiness boundary

Ready now:
- public Python package bootstrap
- repo-local setup flow
- Hermes attach path
- OpenClaw/GoClaw attach docs and native target locations

Not yet universally proven for strangers:
- clean end-user attach inside every external runtime without touching those runtimes
- full upstream GoClaw integration because upstream `internal/channels` currently has unrelated build blockers
