# OpenClaw Attach Guide

## Verdict

OpenClaw attach is no longer just a Python wrapper idea.
There is now a native runtime target in the upstream OpenClaw repo: `~/workspaces/openclaw/extensions/max/`.

## What lives where

This repo:
- proven MAX core contract
- public package/bootstrap/docs
- Hermes integration
- attach contract notes

OpenClaw repo:
- native bundled plugin package
- OpenClaw SDK wiring
- runtime attach surface

## Native OpenClaw entry points

In upstream OpenClaw:
- `extensions/max/index.ts`
- `extensions/max/channel-plugin-api.ts`
- `extensions/max/api.ts`
- `extensions/max/src/channel.ts`
- `extensions/max/src/runtime.ts`

The native package uses:
- `defineBundledChannelEntry(...)`
- `createChatChannelPlugin(...)`
- runtime store / runtime attach methods
- `plugin_factory` equivalent inside the OpenClaw plugin surface

## What is already proven

Local OpenClaw extension tests pass with the MAX plugin package:

```bash
cd ~/workspaces/openclaw
node scripts/run-vitest.mjs run extensions/max/index.ts extensions/max/src/channel.ts
```

Verified result:
- `extensions/max/src/channel.test.ts` → passing

## What is still the honest boundary

Proven:
- native OpenClaw package shape exists
- local OpenClaw channel tests pass
- config/runtime/message attach surface exists

Not yet proven here:
- full end-user attach from a clean external OpenClaw install outside the current upstream workspace
- client-visible MAX traffic through a stranger-owned OpenClaw deployment

## Minimal attach path

1. open the OpenClaw repo
2. configure MAX channel settings (`botToken`, `apiBase`, `webhookUrl`, `webhookSecret`)
3. load the bundled `max` extension
4. start runtime
5. verify outbound text
6. verify inbound webhook

## Useful methods / checks

Expected surface includes:
- `validate_webhook_request`
- `ingest_webhook`
- `status()`
- runtime sendText/startAccount/stopAccount path via the native runtime layer
