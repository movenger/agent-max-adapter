from __future__ import annotations

from enum import StrEnum


class DedupeDecision(StrEnum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"


class InMemoryDedupeStore:
    def __init__(self) -> None:
        self._keys: set[str] = set()

    def has_seen(self, key: str) -> bool:
        return key in self._keys

    def check_and_mark(self, key: str) -> DedupeDecision:
        if self.has_seen(key):
            return DedupeDecision.DUPLICATE
        self._keys.add(key)
        return DedupeDecision.ACCEPTED


class RedisDedupeStore:
    def __init__(self, redis_client: object, namespace: str = "max", ttl_seconds: int = 3600) -> None:
        self.redis_client = redis_client
        self.namespace = namespace
        self.ttl_seconds = ttl_seconds

    def _redis_key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    def check_and_mark(self, key: str) -> DedupeDecision:
        created = self.redis_client.set(self._redis_key(key), "1", ex=self.ttl_seconds, nx=True)
        return DedupeDecision.ACCEPTED if created else DedupeDecision.DUPLICATE


class RedisLikeDedupeStore(RedisDedupeStore):
    def check_and_mark(self, key: str) -> DedupeDecision:
        if hasattr(self.redis_client, "set"):
            return super().check_and_mark(key)
        added = self.redis_client.sadd(self.namespace, key)
        return DedupeDecision.ACCEPTED if added else DedupeDecision.DUPLICATE


def build_dedupe_store(config: object, redis_client: object | None = None) -> object:
    redis_url = getattr(config, "redis_url", None)
    dedupe_ttl_seconds = int(getattr(config, "dedupe_ttl_seconds", 3600))
    if redis_client is not None:
        return RedisLikeDedupeStore(redis_client=redis_client, ttl_seconds=dedupe_ttl_seconds)
    if redis_url:
        from redis import Redis

        client = Redis.from_url(redis_url, decode_responses=True)
        return RedisDedupeStore(redis_client=client, ttl_seconds=dedupe_ttl_seconds)
    return InMemoryDedupeStore()
