from __future__ import annotations

from hermes_max_adapter.models.capabilities import SupportLevel


def build_capability_snapshot() -> dict[str, dict[str, SupportLevel]]:
    return {
        "inbound": {
            "text": SupportLevel.FULL,
            "photo": SupportLevel.FULL,
            "video": SupportLevel.FULL,
            "document": SupportLevel.FULL,
            "audio": SupportLevel.FULL,
            "voice": SupportLevel.FULL,
            "sticker": SupportLevel.FULL,
            "animation": SupportLevel.FULL,
            "location": SupportLevel.DEGRADED,
            "contact": SupportLevel.DEGRADED,
            "callback": SupportLevel.DEGRADED,
            "service": SupportLevel.DEGRADED,
        },
        "outbound": {
            "text": SupportLevel.FULL,
            "buttons": SupportLevel.FULL,
            "photo": SupportLevel.FULL,
            "video": SupportLevel.FULL,
            "document": SupportLevel.FULL,
            "audio": SupportLevel.FULL,
            "voice": SupportLevel.FULL,
            "animation": SupportLevel.FULL,
            "sticker": SupportLevel.FULL,
            "location": SupportLevel.DEGRADED,
            "contact": SupportLevel.DEGRADED,
            "external_url_attachment": SupportLevel.UNKNOWN,
            "local_file_attachment": SupportLevel.UNSUPPORTED,
        },
        "interactions": {
            "callback_receive": SupportLevel.DEGRADED,
            "callback_answer": SupportLevel.DEGRADED,
            "callback_answer_notification": SupportLevel.FULL,
            "callback_answer_show_alert": SupportLevel.DEGRADED,
        },
    }
