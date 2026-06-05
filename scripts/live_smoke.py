from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hermes_max_adapter.client import build_answer_callback_request
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.subscription import build_subscribe_request


def main() -> None:
    config = MaxAdapterConfig.from_env()
    if not config.bot_token or not config.webhook_url:
        print("LIVE_SMOKE_SKIPPED: missing MAX_BOT_TOKEN or MAX_WEBHOOK_URL")
        return
    request = build_subscribe_request(config)
    callback_preview = build_answer_callback_request(
        base_url="https://platform-api.max.ru",
        token=config.bot_token,
        callback_id="preview-callback",
        text="preview",
        notification="toast",
        show_alert=True,
    )
    print("LIVE_SMOKE_READY", request["url"])
    print("CALLBACK_PREVIEW", callback_preview)


if __name__ == "__main__":
    main()
