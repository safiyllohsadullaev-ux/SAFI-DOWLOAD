from utils.helpers import bar, escape_html, format_size
from utils.rate_limit import RateLimiter


def test_escape_and_size():
    assert escape_html("<b>") == "&lt;b&gt;"
    assert format_size(1024) == "1.0 KB"
    assert format_size(49 * 1024 * 1024).endswith("MB")


def test_bar():
    assert bar(0, 10) == "░" * 10
    assert bar(10, 10) == "█" * 10
    assert len(bar(3, 10, 10)) == 10


def test_rate_limiter():
    limiter = RateLimiter(limit=2, window=60)
    assert limiter.hit(1) == 0
    assert limiter.hit(1) == 0
    assert limiter.hit(1) > 0
    assert limiter.hit(2) == 0
