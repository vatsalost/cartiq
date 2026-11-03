"""In-memory sliding window rate limiter for Carti API."""

import time
from collections import defaultdict
from threading import Lock
from typing import Callable
from fastapi import Request
from server.app.core.errors import CartiAPIException, CartiErrorCode


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self.window_seconds = 60
        self.requests = defaultdict(list)
        self.lock = Lock()

    def is_allowed(self, client_key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        with self.lock:
            # Purge timestamps older than the window
            timestamps = [t for t in self.requests[client_key] if t > window_start]
            if len(timestamps) >= self.limit:
                self.requests[client_key] = timestamps
                return False
            timestamps.append(now)
            self.requests[client_key] = timestamps
            return True

    def reset(self) -> None:
        """Reset all recorded request timestamps."""
        with self.lock:
            self.requests.clear()



# Global instances for standard, creation, and auth endpoints
general_limiter = SlidingWindowRateLimiter(requests_per_minute=60)
request_creation_limiter = SlidingWindowRateLimiter(requests_per_minute=10)
auth_limiter = SlidingWindowRateLimiter(requests_per_minute=5)


def rate_limit(limiter: SlidingWindowRateLimiter = general_limiter) -> Callable:
    """FastAPI dependency to enforce rate limits per client IP or user."""

    async def dependency(request: Request):
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )
        key = f"{client_ip}:{request.url.path}"

        if not limiter.is_allowed(key):
            raise CartiAPIException(
                code=CartiErrorCode.RATE_LIMIT_EXCEEDED,
                message="Rate limit exceeded. Please wait a moment before trying again.",
                status_code=429,
                retryable=True,
                details={"retry_after_seconds": 60},
            )

    return dependency
