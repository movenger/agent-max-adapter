from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.env import load_project_env
from hermes_max_adapter.subscription import build_subscription_reconcile_plan


def main() -> None:
    load_project_env(ROOT / ".env")
    config = MaxAdapterConfig.from_env()
    current: list[dict] = []
    plan = build_subscription_reconcile_plan(config, current)
    print(plan)


if __name__ == "__main__":
    main()
