# Hermes Integration Guide

## Purpose

This repo provides a public MAX adapter package for Hermes Agent.
A user should be able to install it from GitHub, set bot/runtime config, attach it, and run smoke checks without project-specific handholding.

## Plugin entrypoint

Runtime entrypoint:
- `src/hermes_max_adapter/plugin.py`

Exports:
- `build_registration()`
- `validate_config()`

Registration metadata includes:
- platform name: `max`
- label: `MAX`
- `required_env = ["MAX_BOT_TOKEN"]`
- `cron_deliver_env_var = "MAX_HOME_CHANNEL"`
- `max_message_length = 4000`
- `adapter_factory`

## Example wiring

```python
from hermes_max_adapter.plugin import build_registration

registration = build_registration()
adapter = registration["adapter_factory"](cfg)
```

Example config shape:

```python
cfg.bot_token = os.environ["MAX_BOT_TOKEN"]
cfg.extra = {
    "token": os.environ["MAX_BOT_TOKEN"],
    "webhook_secret": os.environ.get("MAX_WEBHOOK_SECRET", ""),
    "webhook_url": os.environ.get("MAX_WEBHOOK_URL"),
    "enable_long_polling": False,
}
```

## Local install flow

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e . pytest
cp .env.example .env
python scripts/setup.py
pytest -q
```

## Included verification helpers

These repo scripts auto-load local `.env`:
- `python scripts/live_smoke.py`
- `python scripts/live_outbound_smoke.py`
- `python scripts/watchdog.py`
- `python examples/local_webhook_server.py`

## Current proof level

Proven:
- plugin registration object exists and is tested
- adapter factory exists and is tested
- repo-local setup/install flow exists
- MAX runtime flows are live-confirmed for inbound webhook, text, document, image/photo, and video

Not yet fully proven:
- full end-user install inside every public Hermes distribution variant without any loader-specific adaptation

## Recommended validation after attach

1. plugin registration loads
2. adapter starts from env/config
3. webhook ingress receives MAX events
4. text reply works
5. document/image/video send works
