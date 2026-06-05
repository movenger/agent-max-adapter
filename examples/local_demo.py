from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hermes_max_adapter.adapter import MaxAdapter
from hermes_max_adapter.config import MaxAdapterConfig


class DemoSender:
    def send(self, request: dict) -> dict:
        print("SEND", request)
        return {"status_code": 200, "message_id": "demo-message"}


def main() -> None:
    config = MaxAdapterConfig(
        bot_token="demo-token",
        webhook_secret="demo-secret",
        webhook_url="https://example.com/webhook",
        enable_long_polling=False,
    )
    adapter = MaxAdapter(config=config, sender=DemoSender())
    adapter.connect_sync()
    result = adapter.send_text_sync(chat_id="demo-chat", text="Hello from local demo")
    print(result)
    print(adapter.health_status())


if __name__ == "__main__":
    main()
