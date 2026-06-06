# MAX Multi-Runtime Finish-Up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the MAX adapter as a production-grade multi-runtime integration that Denis can hand to the team for Hermes, OpenClaw, and GoClaw without ambiguity about what is live, what is runtime-ready, and what remains vendor-dependent.

**Architecture:** Hermes remains the canonical transport/runtime implementation. OpenClaw and GoClaw should attach to that transport with runtime-shaped adapters instead of toy stubs. The work must separate transport truth from host-runtime wiring, promote only proven capabilities, and leave explicit degraded behavior where parity is not yet implemented.

**Tech Stack:** Python 3.12, Hermes plugin runtime, TypeScript OpenClaw bundled plugins, Go GoClaw channel manager/runtime, pytest, Vitest, Go test.

---

## File map

### Hermes canonical transport/runtime
- `hermes-max-adapter/src/hermes_max_adapter/plugin.py` — Hermes plugin registration contract.
- `hermes-max-adapter/src/hermes_max_adapter/adapter.py` — canonical MAX runtime adapter.
- `hermes-max-adapter/src/hermes_max_adapter/openclaw.py` — OpenClaw bridge-facing wrapper/helpers.
- `hermes-max-adapter/src/hermes_max_adapter/goclaw.py` — GoClaw bridge-facing wrapper/helpers.
- `hermes-max-adapter/docs/integration/hermes.md` — attach/runtime instructions for Hermes.
- `hermes-max-adapter/docs/integration/openclaw.md` — attach/runtime instructions for OpenClaw.
- `hermes-max-adapter/docs/integration/goclaw.md` — attach/runtime instructions for GoClaw.
- `hermes-max-adapter/docs/runtime-matrix.md` — final readiness matrix across the three runtimes.

### OpenClaw runtime integration
- `openclaw/extensions/max/src/channel.ts` — bundled MAX plugin contract and current runtime stub.
- `openclaw/extensions/max/src/runtime.ts` — runtime bridge entrypoint for OpenClaw-side attach.
- `openclaw/extensions/max/openclaw.plugin.json` — bundled plugin manifest.
- `openclaw/extensions/max/src/channel.test.ts` — bundled MAX plugin verification.
- `openclaw/test/...` — only touch the narrowest release/runtime tests needed if pack/runtime sidecars change.

### GoClaw runtime integration
- `goclaw/internal/channels/max/config.go` — MAX config shape.
- `goclaw/internal/channels/max/config_form.go` — config UI/bus surface.
- `goclaw/internal/channels/max/channel.go` — managed MAX channel implementation.
- `goclaw/internal/channels/max/message_channel.go` — message tool adapter for MAX if needed.
- `goclaw/internal/channels/max/channel_test.go` — MAX channel tests.
- `goclaw/internal/channels/manager.go` — runtime startup/reload/stop wiring.
- `goclaw/internal/config/config.go` — top-level channels config registration.
- `goclaw/cmd/goclaw/main.go` — message tool / event wiring.
- `goclaw/docs/max-channel-truth.md` — task-local truth log.
- `goclaw/docs/max-runtime-integration.md` — operator-facing MAX runtime notes.

---

### Task 1: Freeze the truth boundary before more code

**Files:**
- Modify: `hermes-max-adapter/README.md`
- Create: `hermes-max-adapter/docs/runtime-matrix.md`
- Modify: `goclaw/docs/max-channel-truth.md`

- [ ] **Step 1: Write the runtime matrix doc skeleton**

Create `hermes-max-adapter/docs/runtime-matrix.md` with sections:

```md
# MAX Runtime Matrix

## Hermes
- Transport/runtime status:
- Verified capabilities:
- Unverified or degraded capabilities:

## OpenClaw
- Host runtime status:
- Attached capabilities:
- Missing bridge pieces:

## GoClaw
- Host runtime status:
- Attached capabilities:
- Missing bridge pieces:
```

- [ ] **Step 2: Update README status language to separate Hermes readiness from cross-runtime parity**

Edit `hermes-max-adapter/README.md` so the status block says, in substance:
- Hermes runtime is the canonical working implementation.
- OpenClaw and GoClaw integration layers exist but are still being finalized.
- The repo is the transport source of truth; host runtime parity must be stated separately.

- [ ] **Step 3: Update GoClaw truth log header to mention it is a host-runtime integration log, not transport truth**

Add one sentence near the top of `goclaw/docs/max-channel-truth.md` clarifying:

```md
This file tracks GoClaw host-runtime integration truth only; Hermes transport truth lives in hermes-max-adapter docs.
```

- [ ] **Step 4: Verify docs changed as intended**

Run:
```bash
cd /home/hype/workspaces/hermes-max-adapter && python - <<'PY'
from pathlib import Path
for p in [Path('README.md'), Path('docs/runtime-matrix.md')]:
    print(f'--- {p} ---')
    print(p.read_text()[:1200])
PY
```
Expected: updated wording appears and runtime-matrix doc exists.

---

### Task 2: Audit and promote Hermes bridge-facing wrappers to the canonical attach surface

**Files:**
- Modify: `hermes-max-adapter/src/hermes_max_adapter/openclaw.py`
- Modify: `hermes-max-adapter/src/hermes_max_adapter/goclaw.py`
- Test: `hermes-max-adapter/tests/test_openclaw_bridge.py`
- Test: `hermes-max-adapter/tests/test_goclaw_bridge.py`

- [ ] **Step 1: Read the current bridge wrappers and identify their public attach contract**

Run:
```bash
cd /home/hype/workspaces/hermes-max-adapter && python - <<'PY'
from pathlib import Path
for p in [
    Path('src/hermes_max_adapter/openclaw.py'),
    Path('src/hermes_max_adapter/goclaw.py'),
]:
    print(f'=== {p} ===')
    print(p.read_text()[:4000])
PY
```
Expected: enough context to see whether wrappers are transport-ready or placeholder helpers.

- [ ] **Step 2: Write failing tests for the stable attach helpers you want OpenClaw/GoClaw to depend on**

Create tests that assert, at minimum:
- OpenClaw wrapper can build a runtime-facing config snapshot from env/config fields.
- GoClaw wrapper can build a runtime-facing config snapshot from env/config fields.
- Missing mandatory fields fail closed with explicit error messages.

- [ ] **Step 3: Run the focused failing tests**

Run:
```bash
cd /home/hype/workspaces/hermes-max-adapter && . .venv/bin/activate && pytest -q tests/test_openclaw_bridge.py tests/test_goclaw_bridge.py
```
Expected: RED for the exact bridge contract gap if wrappers are incomplete.

- [ ] **Step 4: Implement the narrowest stable wrapper contract**

Implement helpers that return canonical normalized snapshots such as:
- token
- api_base
- webhook_url
- webhook_secret
- enable_long_polling
- retry/backoff knobs
- dedupe settings when relevant

They should not start servers or mutate global state; they should give host runtimes a stable transport-shaped contract.

- [ ] **Step 5: Re-run bridge tests**

Run:
```bash
cd /home/hype/workspaces/hermes-max-adapter && . .venv/bin/activate && pytest -q tests/test_openclaw_bridge.py tests/test_goclaw_bridge.py
```
Expected: PASS.

---

### Task 3: Replace the OpenClaw MAX runtime stub with a real bridge attachment layer

**Files:**
- Modify: `openclaw/extensions/max/src/channel.ts`
- Modify/Create: `openclaw/extensions/max/src/runtime.ts`
- Test: `openclaw/extensions/max/src/channel.test.ts`

- [ ] **Step 1: Write failing tests for OpenClaw runtime attach behavior**

Add focused tests asserting:
- configured MAX account no longer throws the old “native runtime bridge not wired” stub if the bridge attach layer is present,
- runtime attach fails closed with a host-runtime-specific explicit message when the external bridge process/config cannot be created,
- outbound send path uses the bridge-facing helper rather than the old unconditional stub throw.

- [ ] **Step 2: Run the focused Vitest shard**

Run:
```bash
cd /home/hype/workspaces/openclaw && pnpm -s test:max -- extensions/max/src/channel.test.ts
```
Expected: RED showing the old stub behavior.

- [ ] **Step 3: Implement `runtime.ts` as the OpenClaw-side attach seam**

Implementation requirements:
- isolate host/runtime attach code from pure channel metadata,
- normalize OpenClaw config into the Hermes canonical wrapper shape,
- expose runtime attach helpers used by gateway start/outbound send,
- keep unsupported capabilities explicitly degraded.

- [ ] **Step 4: Replace unconditional stub throws in `channel.ts` with the runtime attach seam**

Specifically:
- `gateway.startAccount` should call the runtime attach helper and fail with a precise attach error if the runtime cannot be created,
- `message.send.text` / outbound send path should route through the attach seam or fail with the same precise attach error,
- keep media false/degraded until separately proven.

- [ ] **Step 5: Re-run the focused OpenClaw MAX shard**

Run:
```bash
cd /home/hype/workspaces/openclaw && pnpm -s test:max -- extensions/max/src/channel.test.ts
```
Expected: PASS.

---

### Task 4: Wire MAX into GoClaw config and channel manager runtime

**Files:**
- Modify: `goclaw/internal/config/config.go`
- Modify: `goclaw/internal/channels/manager.go`
- Modify: `goclaw/cmd/goclaw/main.go`
- Modify/Create: `goclaw/internal/channels/max/message_channel.go`
- Test: `goclaw/internal/channels/max/channel_test.go`

- [ ] **Step 1: Extend top-level GoClaw channels config to include MAX**

Add `Max max.Config` to `ChannelsConfig` and import the new package.

- [ ] **Step 2: Write failing Go tests for manager/config registration**

Add tests that assert:
- `ChannelsConfig` now includes MAX,
- manager start path can evaluate MAX enablement,
- manager stop path publishes `channels.max.stopped` if MAX is running.

- [ ] **Step 3: Run focused Go tests for the MAX package and any new manager test**

Run:
```bash
cd /home/hype/workspaces/goclaw && go test ./internal/channels/max ./internal/channels -run 'Test.*Max|Test.*MAX' -v
```
Expected: RED for missing manager/config wiring.

- [ ] **Step 4: Implement `startMAX` and runtime lifecycle wiring in manager**

Requirements:
- create the MAX channel from config,
- start it when enabled,
- register it in `m.channels`,
- register it with `gw.RegisterChannel`,
- publish `channels.max.started`,
- support stop/reload symmetry with the existing channel patterns.

- [ ] **Step 5: Implement a MAX message tool adapter if the channel is intended to participate in `message` tool routing**

Mirror the existing adapter pattern used by Telegram/HTTP/WhatsApp.
If live send is still intentionally unsupported, the adapter must fail closed with explicit text rather than silently register fake success.

- [ ] **Step 6: Wire `channels.max.started` / `channels.max.stopped` into `cmd/goclaw/main.go`**

If a MAX message adapter exists:
- `messageTool.SetChannel("max", adapter)` on start
- `messageTool.RemoveChannel("max")` on stop

- [ ] **Step 7: Re-run focused Go verification**

Run:
```bash
cd /home/hype/workspaces/goclaw && go test ./internal/channels/max -v
```
Expected: PASS.

Then run:
```bash
cd /home/hype/workspaces/goclaw && go test ./internal/channels -run 'Test.*Max|Test.*MAX' -v
```
Expected: PASS or explicit narrow follow-up if no manager tests exist yet.

---

### Task 5: Write operator-facing integration docs for OpenClaw and GoClaw

**Files:**
- Create: `hermes-max-adapter/docs/integration/openclaw.md`
- Create: `hermes-max-adapter/docs/integration/goclaw.md`
- Modify: `hermes-max-adapter/docs/runtime-matrix.md`
- Modify: `goclaw/docs/max-runtime-integration.md`

- [ ] **Step 1: Document OpenClaw attach path**

Include:
- what config fields OpenClaw expects,
- what the bridge currently supports,
- what capabilities remain degraded,
- what command verifies the attach.

- [ ] **Step 2: Document GoClaw attach path**

Include:
- `channels.max` config shape,
- startup behavior,
- whether message tool routing is attached,
- current fail-closed boundaries.

- [ ] **Step 3: Update runtime matrix with honest readiness states**

Use only three statuses:
- `READY`
- `NEAR-READY`
- `NOT READY`

Populate each runtime with:
- proof command
- proven capabilities
- remaining degraded boundaries

- [ ] **Step 4: Verify docs exist and mention proof commands**

Run:
```bash
cd /home/hype/workspaces/hermes-max-adapter && python - <<'PY'
from pathlib import Path
for p in [
    Path('docs/integration/openclaw.md'),
    Path('docs/integration/goclaw.md'),
    Path('docs/runtime-matrix.md'),
]:
    print(p, p.exists())
PY
```
Expected: all `True`.

---

### Task 6: Final verification and truth closeout

**Files:**
- Modify: `goclaw/docs/max-channel-truth.md`
- Modify: `hermes-max-adapter/docs/runtime-matrix.md`

- [ ] **Step 1: Run Hermes canonical verification**

Run:
```bash
cd /home/hype/workspaces/hermes-max-adapter && . .venv/bin/activate && pytest -q
```
Expected: full suite PASS.

- [ ] **Step 2: Run OpenClaw focused verification**

Run:
```bash
cd /home/hype/workspaces/openclaw && pnpm -s test:max -- extensions/max/src/channel.test.ts
```
Expected: PASS.

- [ ] **Step 3: Run GoClaw focused verification**

Run:
```bash
cd /home/hype/workspaces/goclaw && go test ./internal/channels/max -v
```
Expected: PASS.

- [ ] **Step 4: Update truth docs from fresh evidence only**

Update:
- `goclaw/docs/max-channel-truth.md`
- `hermes-max-adapter/docs/runtime-matrix.md`

Do not leave stale blockers once verification is green.

- [ ] **Step 5: Report the final status in one compressed verdict**

Format:
- Hermes: READY / NEAR-READY / NOT READY
- OpenClaw: READY / NEAR-READY / NOT READY
- GoClaw: READY / NEAR-READY / NOT READY

Each line must include the exact proof command used.
