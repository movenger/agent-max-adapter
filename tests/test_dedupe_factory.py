from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.dedupe import build_dedupe_store, RedisLikeDedupeStore


class FakeRedisWithSAdd:
    def __init__(self) -> None:
        self.values: set[str] = set()

    def sadd(self, namespace: str, key: str) -> int:
        compound = f"{namespace}:{key}"
        if compound in self.values:
            return 0
        self.values.add(compound)
        return 1


def test_build_dedupe_store_returns_memory_when_redis_disabled():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url=None,
        enable_long_polling=False,
        redis_url=None,
    )
    store = build_dedupe_store(config)
    assert store.__class__.__name__ == "InMemoryDedupeStore"


def test_build_dedupe_store_returns_redis_like_when_url_present():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url=None,
        enable_long_polling=False,
        redis_url="redis://localhost:6379/0",
    )
    store = build_dedupe_store(config, redis_client=FakeRedisWithSAdd())
    assert isinstance(store, RedisLikeDedupeStore)
