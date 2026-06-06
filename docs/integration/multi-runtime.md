# Multi-runtime integration notes

## Status
- Hermes runtime integration: implemented and live-confirmed.
- OpenClaw integration: local runtime-shaped plugin package implemented.
- GoClaw integration: local runtime-shaped channel adapter implemented.

## Honest boundary
These OpenClaw and GoClaw layers are **not** yet live-confirmed inside upstream OpenClaw or GoClaw runtimes.
They are local integration layers over the same proven MAX core used by Hermes.

## OpenClaw attach-ready surface
`src/hermes_max_adapter/openclaw.py` now exposes:
- config mapping into `MaxAdapterConfig`
- manifest builder
- registration builder
- plugin factory
- runtime-shaped plugin object with:
  - `start()`
  - `stop()`
  - `status()`
  - `runtime_snapshot()`
  - `attach_checklist()`
  - `validate_webhook_request(...)`
  - `ingest_webhook(...)`
  - `process_update(...)`

This means OpenClaw is no longer just a factory scaffold. It has a local plugin object that can own inbound webhook handling and lifecycle around the proven adapter core.

## GoClaw attach-ready surface
`src/hermes_max_adapter/goclaw.py` exposes:
- config mapping into `MaxAdapterConfig`
- runtime-shaped channel object
- outbound send mapping
- inbound queue mapping from normalized MAX updates
- lifecycle/status methods
- attach helpers:
  - `runtime_snapshot()`
  - `attach_checklist()`

## What is proven vs not proven
### Proven locally
- config mapping into the shared MAX core
- lifecycle shape for OpenClaw and GoClaw wrappers
- webhook request ingestion path for OpenClaw wrapper
- queue-based inbound receive path for GoClaw wrapper
- attach-ready runtime snapshots and local checklists
- tests covering registration/factory/contract behavior

### Not yet proven live
- upstream OpenClaw plugin loading
- upstream OpenClaw runtime dispatch to this package
- upstream GoClaw runtime/channel loading
- end-to-end client-visible delivery through those upstream runtimes

## Next real verification step
To promote either runtime from local-ready to runtime-proven, this package must be mounted into the real upstream runtime for OpenClaw or GoClaw and exercised end-to-end there.
