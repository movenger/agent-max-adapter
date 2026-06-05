from hermes_max_adapter.dedupe import DedupeDecision, RedisLikeDedupeStore


class FakeRedis:
    def __init__(self) -> None:
        self.store: set[str] = set()

    def sadd(self, key: str, value: str) -> int:
        compound = f"{key}:{value}"
        if compound in self.store:
            return 0
        self.store.add(compound)
        return 1


def test_redis_like_dedupe_store_marks_duplicates():
    store = RedisLikeDedupeStore(redis_client=FakeRedis(), namespace="max")
    first = store.check_and_mark("message_created:1")
    second = store.check_and_mark("message_created:1")
    assert first == DedupeDecision.ACCEPTED
    assert second == DedupeDecision.DUPLICATE
