# Hermes Integration Guide

## Purpose

This repo provides a MAX platform adapter plugin for Hermes Agent.

## Plugin entrypoint

Runtime entrypoint:
- `src/hermes_max_adapter/plugin.py`

Exported registration:
- `build_registration()`

Registration metadata includes:
- platform name: `max`
- label: `MAX`
- `required_env = ["MAX_BOT_TOKEN"]`
- `validate_config`
- `adapter_factory`
- `cron_deliver_env_var = "MAX_HOME_CHANNEL"`
- `max_message_length = 4000`

## Adapter factory behavior

`adapter_factory` builds `MaxAdapter` using:
- bot token
- webhook secret
- webhook URL
- long polling flag

## Example wiring shape

Hermes-side config object should provide:

```python
cfg.bot_token = os.environ["MAX_BOT_TOKEN"]
cfg.extra = {
    "token": os.environ["MAX_BOT_TOKEN"],
    "webhook_secret": os.environ.get("MAX_WEBHOOK_SECRET", ""),
    "webhook_url": os.environ.get("MAX_WEBHOOK_URL"),
    "enable_long_polling": False,
}
```

Then:

```python
registration = build_registration()
adapter = registration["adapter_factory"](cfg)
```

## Runtime expectation

Hermes plugin loader should:
1. import the plugin module
2. call `build_registration()`
3. use `adapter_factory(...)` to instantiate the adapter
4. call adapter lifecycle methods (`connect`, `disconnect`, `send`, `get_chat_info`)

## Current proof level

What is proven:
- plugin registration object exists and is tested
- adapter factory exists and is tested
- MAX runtime flows are live-confirmed for text, document, image/photo, video, and inbound webhook

What is not yet fully proven:
- a complete end-user install of this package inside a real public Hermes gateway distribution with final loader wiring

## Recommended validation after integration

After wiring into Hermes, verify:
1. plugin registration loads successfully
2. adapter starts with env config
3. webhook ingress receives MAX events
4. Hermes can send a text reply
5. Hermes can send document/image/video through the adapter
