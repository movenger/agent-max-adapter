from hermes_max_adapter.dedupe import DedupeDecision, InMemoryDedupeStore


def test_dedupe_store_marks_second_occurrence_as_duplicate():
    store = InMemoryDedupeStore()
    first = store.check_and_mark("message_created:123")
    second = store.check_and_mark("message_created:123")
    assert first == DedupeDecision.ACCEPTED
    assert second == DedupeDecision.DUPLICATE


def test_dedupe_store_can_check_without_marking():
    store = InMemoryDedupeStore()
    assert store.has_seen("message_created:123") is False
    store.check_and_mark("message_created:123")
    assert store.has_seen("message_created:123") is True
