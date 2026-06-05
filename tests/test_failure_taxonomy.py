from hermes_max_adapter.client import classify_send_response


def test_classify_send_response_marks_success_for_200():
    result = classify_send_response({"status_code": 200, "message_id": "m1"})
    assert result["success"] is True
    assert result["retryable"] is False


def test_classify_send_response_marks_retryable_for_429():
    result = classify_send_response({"status_code": 429, "error": "rate limited"})
    assert result["success"] is False
    assert result["retryable"] is True


def test_classify_send_response_marks_non_retryable_for_400():
    result = classify_send_response({"status_code": 400, "error": "bad request"})
    assert result["success"] is False
    assert result["retryable"] is False
