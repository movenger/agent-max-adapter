from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.dedupe import build_dedupe_store


def main() -> None:
    config = MaxAdapterConfig.from_env()
    if not config.redis_url:
        print("REDIS_SMOKE_SKIPPED: missing REDIS_URL")
        return
    store = build_dedupe_store(config)
    result1 = store.check_and_mark("smoke-key")
    result2 = store.check_and_mark("smoke-key")
    print("REDIS_SMOKE", result1.value, result2.value)


if __name__ == "__main__":
    main()
