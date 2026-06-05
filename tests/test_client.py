from hermes_max_adapter.client import build_answer_callback_request, build_send_request




def test_build_send_request_uses_messages_endpoint_and_auth_header():
    request = build_send_request(
        base_url="https://platform-api.max.ru",
        token="secret",
        user_id=42,
        payload={"text": "hi"},
    )
    assert request["method"] == "POST"
    assert request["url"] == "https://platform-api.max.ru/messages?user_id=42"
    assert request["headers"]["Authorization"] == "secret"
    assert request["headers"]["Content-Type"] == "application/json"
    assert request["json"] == {"text": "hi"}


def test_build_send_request_supports_chat_id_targeting():
    request = build_send_request(
        base_url="https://platform-api.max.ru",
        token="secret",
        user_id=None,
        chat_id=99,
        payload={"text": "hi"},
    )
    assert request["url"] == "https://platform-api.max.ru/messages?chat_id=99"


def test_build_send_request_rejects_non_numeric_target_ids():
    try:
        build_send_request(
            base_url="https://platform-api.max.ru",
            token="secret",
            chat_id="preview-chat",
            payload={"text": "hi"},
        )
    except ValueError as exc:
        assert "integer" in str(exc)
    else:
        raise AssertionError("Expected ValueError for non-numeric MAX target id")


def test_build_answer_callback_request_supports_optional_vendor_flags():
    request = build_answer_callback_request(
        base_url="https://platform-api.max.ru",
        token="secret",
        callback_id="cb-1",
        text="done",
        notification="toast",
        show_alert=True,
    )
    assert request["method"] == "POST"
    assert request["url"] == "https://platform-api.max.ru/answers?callback_id=cb-1&message=done"
    assert request["headers"]["Authorization"] == "secret"
    assert request["json"] == {
        "notification": "toast",
        "show_alert": "true",
    }
