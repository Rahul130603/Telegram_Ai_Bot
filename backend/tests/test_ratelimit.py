from app.utils.ratelimit import SlidingWindowRateLimiter


def test_sliding_window():
    limiter = SlidingWindowRateLimiter(2, 10)
    assert limiter.allow(1, 0) and limiter.allow(1, 1)
    assert not limiter.allow(1, 2)
    assert limiter.allow(1, 11)

