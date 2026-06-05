from __future__ import annotations


def build_source_descriptor(
    chat_id: str,
    user_id: str,
    user_name: str,
    chat_type: str,
    chat_name: str,
) -> dict[str, str]:
    return {
        "chat_id": chat_id,
        "user_id": user_id,
        "user_name": user_name,
        "chat_type": chat_type,
        "chat_name": chat_name,
    }
