
import time
import math
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):

    WINDOW_SECONDS = 60

    # Maximum requests allowed per client within 60 seconds
    LIMITS = {
        "auth": 5,
        "prescriptions": 20,
        "assistant": 20,
        "general": 100
    }

    def __init__(self, app):
        super().__init__(app)

        # Stores request timestamps for each client and category
        self.requests = defaultdict(deque)

        # Protect shared storage from concurrent access
        self.lock = Lock()

        self.last_cleanup = time.monotonic()

    def get_category(self, path: str) -> str:

        if path in {
            "/auth/login",
            "/auth/register",
            "/auth/token"
        }:
            return "auth"

        if path == "/prescriptions" or path.startswith("/prescriptions/"):
            return "prescriptions"

        if path == "/assistant" or path.startswith("/assistant/"):
            return "assistant"

        return "general"

    def get_client_ip(self, request) -> str:

        if request.client:
            return request.client.host

        return "unknown"

    def check_rate_limit(self, client_ip: str, category: str):

        now = time.monotonic()

        window_start = now - self.WINDOW_SECONDS

        limit = self.LIMITS[category]

        key = (client_ip, category)

        with self.lock:

            # Remove expired entries for this client
            timestamps = self.requests[key]

            while timestamps and timestamps[0] <= window_start:
                timestamps.popleft()

            # Periodically clean up inactive clients
            if now - self.last_cleanup >= self.WINDOW_SECONDS:

                for stored_key in list(self.requests.keys()):

                    stored_timestamps = self.requests[stored_key]

                    while (
                        stored_timestamps
                        and stored_timestamps[0] <= window_start
                    ):
                        stored_timestamps.popleft()

                    if not stored_timestamps:
                        del self.requests[stored_key]

                self.last_cleanup = now

                # Re-fetch the current client's deque
                timestamps = self.requests[key]

            # Check whether the limit has been exceeded
            if len(timestamps) >= limit:

                retry_after = math.ceil(
                    self.WINDOW_SECONDS - (now - timestamps[0])
                )

                return False, 0, retry_after, limit

            # Record the current request
            timestamps.append(now)

            remaining = limit - len(timestamps)

            return True, remaining, 0, limit

    async def dispatch(self, request, call_next):

        # Don't count CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        category = self.get_category(request.url.path)

        client_ip = self.get_client_ip(request)

        allowed, remaining, retry_after, limit = (
            self.check_rate_limit(client_ip, category)
        )

        if not allowed:

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later."
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0"
                }
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
