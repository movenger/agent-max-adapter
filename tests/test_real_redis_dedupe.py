from hermes_max_adapter.config import MaxAdapterConfig
from hermes_max_adapter.dedupe import build_dedupe_store, RedisDedupeStore


class FakeRedisWithExpiry:
    def __init__(self) -> None:
        self.keys: dict[str, int] = {}
        self.expiry: dict[str, int] = {}

    def set(self, key: str, value: str, ex: int, nx: bool = False):
        if nx and key in self.keys:
            return False
        self.keys[key] = 1
        self.expiry[key] = ex
        return True


def test_redis_dedupe_store_uses_set_nx_with_ttl():
    redis_client = FakeRedisWithExpiry()
    store = RedisDedupeStore(redis_client=redis_client, namespace="max", ttl_seconds=3600)

    first = store.check_and_mark("message_created:1")
    second = store.check_and_mark("message_created:1")

    assert first.value == "accepted"
    assert second.value == "duplicate"
    assert redis_client.expiry["max:message_created:1"] == 3600


def test_build_dedupe_store_uses_real_redis_when_url_present():
    config = MaxAdapterConfig(
        bot_token="token",
        webhook_secret="secret",
        webhook_url=None,
        enable_long_polling=False,
        redis_url="redis://localhost:6379/0",
        dedupe_ttl_seconds=600,
    )
    store = build_dedupe_store(config, redis_client=FakeRedisWithExpiry())
    assert isinstance(store, RedisDedupeStore)
