# Quick Attach Guide

## Fastest path

1. clone the repo
2. create `.venv`
3. install the package
4. run setup wizard
5. wire plugin registration into Hermes

## Copy-paste bootstrap

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e . pytest
cp .env.example .env
python scripts/setup.py
pytest -q
```

## Minimum env

```bash
export MAX_BOT_TOKEN="..."
export MAX_WEBHOOK_SECRET="dev-secret"
export MAX_WEBHOOK_URL="https://your-domain.example/max/webhook"
```

## Conceptual Hermes wiring

```python
from hermes_max_adapter.plugin import build_registration

registration = build_registration()
adapter = registration["adapter_factory"](cfg)
```

## First post-attach checks

- plugin registration loads
- adapter starts
- webhook receives an inbound event
- text send works
- document/image/video sends work
```
