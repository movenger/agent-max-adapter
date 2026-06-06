# OpenClaw MAX Integration

OpenClaw now has a bundled `max` channel that uses a **runtime attach seam** instead of the old unconditional stub throw.

This means OpenClaw is no longer at the "toy placeholder" stage. But it is still **not full live runtime parity** with Hermes yet.

## Status

Current status: **NEAR-READY**.

What is proven:
- bundled MAX plugin package exists under `extensions/max/`
- channel metadata/config/security/pairing surfaces exist
- `gateway.startAccount(...)` routes through the MAX runtime attach seam
- outbound text routes through the same runtime seam
- missing runtime or missing runtime methods fail closed with explicit attach errors

What remains degraded:
- media delivery
- pairing notification delivery
- real OpenClaw-hosted inbound lifecycle proof
- full runtime parity beyond the attach seam

## Config shape

Minimal OpenClaw config section:

```json
{
  "channels": {
    "max": {
      "enabled": true,
      "botToken": "YOUR_MAX_BOT_TOKEN",
      "apiBase": "https://botapi.max.ru",
      "webhookUrl": "https://example.com/max/webhook",
      "webhookSecret": "YOUR_MAX_WEBHOOK_SECRET",
      "allowFrom": ["123456789"],
      "dmPolicy": "pairing"
    }
  }
}
```

## What the bridge currently supports

The OpenClaw MAX runtime seam currently supports:
- config normalization into the canonical MAX runtime shape
- account attach / start through `runtime.ts`
- account stop through `runtime.ts`
- outbound text through `sendMaxText(...)`
- explicit attach errors when runtime pieces are missing

The seam does **not** currently promote:
- media send
- reactions
- edits
- threads
- pairing notifications

Those remain intentionally degraded.

## Attach behavior

When `gateway.startAccount(...)` runs for MAX:
- OpenClaw resolves `channels.max` config into a normalized MAX account snapshot
- it checks whether the account is configured (`botToken`, `apiBase`, `webhookUrl`)
- it calls `startMaxAccount(...)` from `runtime.ts`
- `runtime.ts` delegates to the plugin runtime if the runtime exposes `startAccount` or `attachAccount`
- if the runtime is missing, OpenClaw fails with an explicit attach error instead of pretending startup worked

Outbound text follows the same pattern through `sendMaxText(...)`.

## Current fail-closed boundary

OpenClaw still fails closed when:
- MAX runtime is not initialized
- runtime does not expose `attachAccount` / `startAccount`
- runtime does not expose `sendText`
- account config is incomplete

That is the correct behavior for now: attach-ready, but honest.

## Proof command

Fresh focused proof command:

```bash
cd /home/hype/workspaces/openclaw && pnpm -s test:max -- extensions/max/src/channel.test.ts
```

This verifies:
- startAccount uses the runtime attach seam
- missing runtime produces explicit attach failure
- outbound send routes through runtime seam
- bundled plugin metadata/capabilities are still guarded honestly

## What remains before OpenClaw can be called READY

OpenClaw still needs:
1. real runtime-backed inbound lifecycle proof
2. media capability promotion only after proof
3. pairing notification wiring
4. broader runtime verification beyond the focused MAX shard

Until then, the honest state is **NEAR-READY**.
