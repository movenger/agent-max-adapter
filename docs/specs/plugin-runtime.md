# Plugin runtime notes

## Current runtime shape

- `plugin.py` exposes `build_registration()`
- registration includes `adapter_factory`
- registration includes `validate_config`
- adapter exposes async `connect`, `disconnect`, `send`, `get_chat_info`

## Intended Hermes wiring

- Hermes plugin loader should call registration entrypoint
- runtime should instantiate adapter through `adapter_factory`
- env/config should provide token, webhook URL, and retry policy

## Remaining gap

- This repo is runtime-shaped for Hermes, but not yet installed/tested inside a real Hermes gateway process
