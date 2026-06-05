from __future__ import annotations

from urllib.parse import urlencode


def _normalize_max_target_id(value: int | str | None, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized or not normalized.isdigit():
        raise ValueError(f"MAX {field_name} must be an integer-compatible identifier")
    return normalized


def build_send_request(
    base_url: str,
    token: str,
    payload: dict,
    user_id: int | str | None = None,
    chat_id: int | str | None = None,
) -> dict:
    params: dict[str, str] = {}
    normalized_user_id = _normalize_max_target_id(user_id, "user_id")
    normalized_chat_id = _normalize_max_target_id(chat_id, "chat_id")
    if normalized_user_id is not None:
        params["user_id"] = normalized_user_id
    if normalized_chat_id is not None:
        params["chat_id"] = normalized_chat_id
    query = urlencode(params)
    url = f"{base_url}/messages"
    if query:
        url = f"{url}?{query}"
    return {
        "method": "POST",
        "url": url,
        "headers": {
            "Authorization": token,
            "Content-Type": "application/json",
        },
        "json": payload,
    }


def build_answer_callback_request(
    base_url: str,
    token: str,
    callback_id: str,
    text: str | None = None,
    notification: str | None = None,
    show_alert: bool | None = None,
) -> dict:
    query_params = {"callback_id": callback_id}
    if text is not None:
        query_params["message"] = text
    query = urlencode(query_params)
    payload: dict[str, str] = {}
    if notification is not None:
        payload["notification"] = notification
    if show_alert is not None:
        payload["show_alert"] = "true" if show_alert else "false"
    return {
        "method": "POST",
        "url": f"{base_url}/answers?{query}",
        "headers": {
            "Authorization": token,
            "Content-Type": "application/json",
        },
        "json": payload,
    }


def classify_send_response(response: dict) -> dict:
    status_code = int(response.get("status_code", 500))
    success = 200 <= status_code < 300
    retryable = status_code in {408, 425, 429, 500, 502, 503, 504}
    return {
        "success": success,
        "retryable": retryable if not success else False,
        "status_code": status_code,
        "message_id": response.get("message_id"),
        "error": response.get("error"),
    }
