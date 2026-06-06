# GoClaw MAX Integration

GoClaw now includes MAX in config, channel manager lifecycle, and message-tool hot-reload wiring.

This is enough to call the GoClaw side **attach-ready and NEAR-READY**, but not enough to claim live MAX traffic from GoClaw.

## Status

Current status: **NEAR-READY**.

What is proven:
- `channels.max` exists in top-level GoClaw config
- manager startup/reload/stop wiring includes MAX
- `channels.max.started` / `channels.max.stopped` are published
- the message tool can attach and remove a MAX adapter dynamically
- focused Go verification passes

What remains degraded:
- real MAX outbound delivery
- inbound webhook/polling lifecycle in GoClaw
- user mapping and live chat flow
- edit/delete/react/media via real runtime bridge

## Config shape

Minimal `goclaw.json` section:

```json
{
  "channels": {
    "max": {
      "enabled": true,
      "botToken": "YOUR_MAX_BOT_TOKEN",
      "apiBase": "https://botapi.max.ru",
      "webhookUrl": "https://example.com/max/webhook",
      "webhookSecret": "YOUR_MAX_WEBHOOK_SECRET",
      "defaultChatId": "123456789"
    }
  }
}
```

## Startup behavior

When MAX is enabled:
- GoClaw creates the MAX managed channel
- `startMAX(...)` evaluates the config
- manager registers the channel in `m.channels`
- manager registers it with the gateway
- GoClaw publishes `channels.max.started`
- message-tool hot-reload attaches the MAX adapter

On stop/reload:
- GoClaw stops the MAX channel
- unregisters it from the gateway
- removes it from the manager map
- publishes `channels.max.stopped`
- removes the adapter from the message tool

## Message tool routing

MAX now participates in message-tool lifecycle.

Current adapter behavior:
- validates `chatID` as an integer-compatible string
- resolves `./media/...` paths against the runtime media base
- returns explicit fail-closed errors for send/edit/delete/react while runtime bridge is still absent

That is intentional. The adapter is attached, but it does not fake real delivery.

## Current fail-closed boundary

GoClaw still does **not** have:
- a real MAX runtime bridge behind the managed channel
- live outbound send through MAX transport
- inbound webhook or polling runtime
- client-visible proof of GoClaw-side MAX delivery

So the correct state is attach-ready, not production-live.

## Proof commands

Focused MAX package + manager proof:

```bash
cd /home/hype/workspaces/goclaw && go test -vet=off ./internal/channels/max ./internal/channels -run 'Test.*Max|Test.*MAX' -v
```

Main wiring proof:

```bash
cd /home/hype/workspaces/goclaw && go test -vet=off ./cmd/goclaw -run Test.*Max -v
```

## What remains before GoClaw can be called READY

GoClaw still needs:
1. real runtime bridge attachment behind the managed channel
2. real outbound send wired to MAX transport
3. inbound runtime path (webhook or polling)
4. client-visible proof that GoClaw MAX traffic works end-to-end

Until then, the honest state is **NEAR-READY**.
