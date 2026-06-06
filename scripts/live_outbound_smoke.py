from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hermes_max_adapter.client import build_answer_callback_request, build_send_request
from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.env import load_project_env
from hermes_max_adapter.models.attachments import AttachmentKind, AttachmentRef, AttachmentSourceKind
from hermes_max_adapter.upload import build_outbound_attachment_payload


class PreviewSender:
    def send(self, request: dict) -> dict:
        print("OUTBOUND_REQUEST", request)
        return {"status_code": 200, "message_id": "preview-message"}


def main() -> None:
    load_project_env(ROOT / ".env")
    config = MaxAdapterConfig.from_env()
    if not config.bot_token:
        print("LIVE_OUTBOUND_SMOKE_SKIPPED: missing MAX_BOT_TOKEN")
        return
    print("LIVE_OUTBOUND_SMOKE_READY: provide a real numeric chat_id/user_id before live send")

    token_preview = build_outbound_attachment_payload(
        AttachmentRef(kind=AttachmentKind.PHOTO, source=AttachmentSourceKind.VENDOR_TOKEN, upload_token="preview-photo-token")
    )
    url_preview = build_outbound_attachment_payload(
        AttachmentRef(kind=AttachmentKind.DOCUMENT, source=AttachmentSourceKind.EXTERNAL_URL, url="https://example.com/file.pdf")
    )
    callback_preview = build_answer_callback_request(
        base_url="https://platform-api.max.ru",
        token=config.bot_token,
        callback_id="preview-callback",
        text="preview",
        notification="toast",
        show_alert=True,
    )
    send_preview = build_send_request(
        base_url="https://platform-api.max.ru",
        token=config.bot_token,
        chat_id=1,
        payload={"text": "token-only outbound smoke", "attachments": [token_preview, url_preview]},
    )

    sender = PreviewSender()
    sender.send(send_preview)
    print("CALLBACK_REQUEST", callback_preview)
    print("LIVE_OUTBOUND_SMOKE_READY")


if __name__ == "__main__":
    main()
