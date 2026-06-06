# GoClaw Attach Guide

## Verdict

GoClaw attach has a native runtime target now: `~/workspaces/goclaw/internal/channels/max/`.
But full upstream attach is still blocked by unrelated build debt in GoClaw's wider `internal/channels` package.

## What lives where

This repo:
- proven MAX core contract
- public Python package/bootstrap/docs
- Hermes integration
- contract model for GoClaw attach

GoClaw repo:
- native Go MAX channel
- manager/config wiring
- runtime delivery interfaces

## Native GoClaw target

In upstream GoClaw the real runtime-native implementation lives under:
- `internal/channels/max/channel.go`
- `internal/channels/max/config.go`
- `internal/channels/max/config/config.go`
- `internal/channels/max/config_form.go`
- `internal/channels/manager_max_test.go`

For the public attach contract exposed from this repo, the key surface is:
- `create_goclaw_channel(...)`
- `GoClawOutboundMessage`
- `Status()` / `status()`
- `Receive()` / `receive_nowait()`
- `push_update(...)`

## What is proven

Focused package proof:

```bash
cd ~/workspaces/goclaw
go test ./internal/channels/max -count=1
```

This passes.

## What is blocked

Broader attach proof:

```bash
go test ./internal/channels ./internal/channels/max -run TestMAX -count=1
```

Current blocker:
- pre-existing logging-format build errors in upstream `internal/channels/manager.go`
- this is a workspace blocker, not specific evidence that the MAX package itself is broken

## Honest boundary

Proven:
- native Go MAX package exists
- focused package-level proof works
- channel is present as a real GoClaw-side integration target

Not yet proven:
- clean full upstream `internal/channels` verification until manager build debt is fixed
- end-user attach from a stranger-owned GoClaw setup with client-visible MAX traffic

## What to verify next in GoClaw

1. fix or isolate upstream `manager.go` logging-format blocker
2. rerun wider `internal/channels` verification
3. start GoClaw with MAX enabled
4. verify outbound send
5. verify inbound webhook/runtime path
