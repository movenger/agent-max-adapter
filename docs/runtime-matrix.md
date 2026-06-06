# MAX Runtime Matrix

## Hermes
- Status: READY
- Proof command:
  - `cd /home/hype/workspaces/hermes-max-adapter && . .venv/bin/activate && pytest -q`
- Proven capabilities:
  - inbound webhook delivery
  - outbound text
  - outbound document
  - outbound image/photo
  - outbound video
  - Hermes plugin registration and adapter factory
- Remaining degraded boundaries:
  - full public end-user install proof inside an external Hermes distribution is still not the primary verification layer

## OpenClaw
- Status: NEAR-READY
- Proof command:
  - `cd /home/hype/workspaces/openclaw && pnpm -s test:max -- extensions/max/src/channel.test.ts`
- Proven capabilities:
  - bundled MAX plugin manifest/package shape exists
  - config/security/pairing/plugin metadata surfaces exist
  - `gateway.startAccount(...)` uses the runtime attach seam
  - outbound text uses the runtime attach seam
  - missing runtime fails closed with explicit attach errors
- Remaining degraded boundaries:
  - media delivery
  - pairing notification delivery
  - broader live inbound/outbound host-runtime proof beyond the focused shard

## GoClaw
- Status: NEAR-READY
- Proof commands:
  - `cd /home/hype/workspaces/goclaw && go test -vet=off ./internal/channels/max -v`
  - `cd /home/hype/workspaces/goclaw && go test -vet=off ./internal/channels -run 'Test.*Max|Test.*MAX' -v`
  - `cd /home/hype/workspaces/goclaw && go test -vet=off ./cmd/goclaw -run Test.*Max -v`
- Proven capabilities:
  - `channels.max` exists in top-level config
  - manager startup/reload/stop wiring includes MAX
  - `channels.max.started` / `channels.max.stopped` publish correctly
  - message-tool adapter attaches/removes on channel lifecycle
  - adapter validates `chatID`, resolves media path, and fail-closes honestly
- Remaining degraded boundaries:
  - real runtime bridge behind the managed channel
  - real outbound send/edit/delete/react through MAX transport
  - inbound webhook/polling runtime and client-visible proof
