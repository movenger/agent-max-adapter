from hermes_max_adapter.dedupe import DedupeDecision, InMemoryDedupeStore
from hermes_max_adapter.updates import normalize_update


def test_duplicate_update_processed_once():
    store = InMemoryDedupeStore()
    payload = {
        "update_type": "message_created",
        "chat_id": "c1",
        "user_id": "u1",
        "message": {"body": {"text": "hello"}},
        "mid": "m1",
    }
    key = f"{payload['update_type']}:{payload['mid']}"
    first = store.check_and_mark(key)
    second = store.check_and_mark(key)
    event = normalize_update(payload)

    assert first == DedupeDecision.ACCEPTED
    assert second == DedupeDecision.DUPLICATE
    assert event.text == "hello"
