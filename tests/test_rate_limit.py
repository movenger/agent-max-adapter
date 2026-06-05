from hermes_max_adapter.rate_limit import TokenBucketRateLimiter


def test_rate_limiter_allows_up_to_capacity():
    limiter = TokenBucketRateLimiter(rate_per_second=2, capacity=2)
    assert limiter.try_acquire(now=0.0) is True
    assert limiter.try_acquire(now=0.0) is True
    assert limiter.try_acquire(now=0.0) is False


def test_rate_limiter_refills_over_time():
    limiter = TokenBucketRateLimiter(rate_per_second=2, capacity=2)
    limiter.try_acquire(now=0.0)
    limiter.try_acquire(now=0.0)
    assert limiter.try_acquire(now=0.0) is False
    assert limiter.try_acquire(now=0.5) is True
