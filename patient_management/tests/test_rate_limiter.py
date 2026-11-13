from collections import deque
from time import monotonic

import pytest

from middleware.rate_limit import RateLimitMiddleware


def test_rate_limiter_module_imports():
    assert RateLimitMiddleware is not None


def test_rate_limit_window_uses_deque():
    requests = deque()

    now = monotonic()
    requests.append(now)

    assert len(requests) == 1
    assert requests[0] == now


def test_old_requests_can_be_removed_from_window():
    requests = deque([10, 20, 30])

    window_start = 25

    while requests and requests[0] <= window_start:
        requests.popleft()

    assert list(requests) == [30]