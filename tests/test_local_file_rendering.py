from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hermes_max_adapter.models.attachments import AttachmentKind, AttachmentRef, AttachmentSourceKind
from hermes_max_adapter.models.max_messages import OutboundAttachmentPart, OutboundMessage
from hermes_max_adapter.renderer import render_canonical_outbound_message


def test_render_canonical_outbound_message_rejects_local_file_attachment_without_upload_resolution():
    message = OutboundMessage(
        target_chat_id="1",
        parts=[
            OutboundAttachmentPart(
                attachment=AttachmentRef(
                    kind=AttachmentKind.DOCUMENT,
                    source=AttachmentSourceKind.LOCAL_FILE,
                    local_path="/tmp/probe.txt",
                )
            )
        ],
    )

    try:
        render_canonical_outbound_message(message)
    except ValueError as exc:
        assert "requires vendor upload" in str(exc)
    else:
        raise AssertionError("expected local file attachment to require upload resolution before rendering")
