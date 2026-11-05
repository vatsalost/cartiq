"""HTTP client wrapper with connection pooling, retries, and error mapping."""

import asyncio
import logging
from typing import Any, Optional
import httpx
from modules.b6_channel3.client.authentication import Channel3Auth
from modules.b6_channel3.config import Channel3Config
from modules.b6_channel3.constants import RETRYABLE_STATUS_CODES
from modules.b6_channel3.exceptions import (
    Channel3AuthError,
    Channel3BadRequestError,
    Channel3Error,
    Channel3NetworkError,
    Channel3NotFoundError,
    Channel3RateLimitError,
    Channel3ServerError,
    Channel3TimeoutError,
)

logger = logging.getLogger("cartiq.channel3.http")


class Channel3HTTPClient:
    """Async HTTP client for communicating with Channel3 API."""

    def __init__(
        self,
        config: Optional[Channel3Config] = None,
        auth: Optional[Channel3Auth] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.config = config or Channel3Config()
        self.auth = auth or Channel3Auth(self.config.api_key)

        limits = httpx.Limits(
            max_connections=20,
            max_keepalive_connections=10,
            keepalive_expiry=30.0,
        )
        timeout = httpx.Timeout(
            timeout=self.config.timeout_seconds,
            connect=self.config.connect_timeout_seconds,
        )

        self._client = httpx.AsyncClient(
            base_url=self.config.base_url.rstrip("/"),
            limits=limits,
            timeout=timeout,
            transport=transport,
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "Channel3HTTPClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    def _sanitize_headers_for_logging(self, headers: dict[str, str]) -> dict[str, str]:
        """Strip sensitive credentials before logging."""
        sanitized = {}
        for k, v in headers.items():
            if k.lower() in ("x-api-key", "authorization", "proxy-authorization"):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = v
        return sanitized

    async def request(
        self,
        method: str,
        path: str,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Execute HTTP request with retries and exception mapping.

        Args:
            method: HTTP verb ('GET', 'POST').
            path: Relative URL path (e.g. '/v1/search').
            json: JSON body dictionary for POST.
            params: Query parameters dictionary.

        Returns:
            Parsed JSON response dictionary.

        Raises:
            Channel3AuthError, Channel3RateLimitError, Channel3NotFoundError,
            Channel3ServerError, Channel3BadRequestError, Channel3TimeoutError,
            Channel3NetworkError, Channel3Error.
        """
        headers = self.auth.get_auth_headers()
        max_attempts = max(1, self.config.max_retries + 1)
        attempt = 0
        last_exception: Optional[Exception] = None

        while attempt < max_attempts:
            attempt += 1
            try:
                response = await self._client.request(
                    method=method,
                    url=path,
                    headers=headers,
                    json=json,
                    params=params,
                )

                # Success
                if response.status_code == 200 or response.status_code == 201:
                    try:
                        return response.json()
                    except Exception as e:
                        raise Channel3ServerError(
                            f"Channel3 returned invalid JSON: {e}",
                            status_code=response.status_code,
                        ) from e

                # Map error codes
                status = response.status_code

                if status in (401, 403):
                    raise Channel3AuthError(
                        f"Authentication failed with status {status}. Verify API key configuration.",
                        status_code=status,
                    )

                if status == 404:
                    raise Channel3NotFoundError(
                        f"Resource at '{path}' was not found (HTTP 404).",
                        status_code=404,
                    )

                if status == 400:
                    try:
                        err_body = response.json()
                        err_msg = err_body.get("message") or err_body.get("error") or response.text
                    except Exception:
                        err_msg = response.text
                    raise Channel3BadRequestError(f"Bad request (HTTP 400): {err_msg}", status_code=400)

                # Retryable status codes (429 rate limit or 5xx server errors)
                if status in RETRYABLE_STATUS_CODES:
                    retry_after_sec = None
                    if status == 429:
                        raw_retry = response.headers.get("Retry-After")
                        if raw_retry and raw_retry.isdigit():
                            retry_after_sec = float(raw_retry)

                    if attempt < max_attempts:
                        delay = (
                            retry_after_sec
                            if retry_after_sec is not None
                            else self.config.backoff_factor * (2 ** (attempt - 1))
                        )
                        # Cap backoff delay to 10 seconds
                        delay = min(delay, 10.0)
                        logger.warning(
                            "Channel3 API transient failure (status %d) on %s. Retrying in %.2fs (attempt %d/%d)...",
                            status,
                            path,
                            delay,
                            attempt,
                            max_attempts,
                        )
                        await asyncio.sleep(delay)
                        continue

                    # Exhausted retries for 429
                    if status == 429:
                        raise Channel3RateLimitError(
                            "Channel3 rate limit exceeded (HTTP 429) after retries.",
                            retry_after=retry_after_sec,
                        )

                    # Exhausted retries for 5xx
                    raise Channel3ServerError(
                        f"Channel3 server error (HTTP {status}) after {attempt} attempts.",
                        status_code=status,
                    )

                # Unexpected client/server error
                raise Channel3Error(
                    f"Unexpected HTTP {status} response from Channel3: {response.text[:200]}",
                    status_code=status,
                )

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
                last_exception = e
                if attempt < max_attempts:
                    delay = self.config.backoff_factor * (2 ** (attempt - 1))
                    await asyncio.sleep(min(delay, 5.0))
                    continue
                raise Channel3TimeoutError(f"Channel3 request timed out after {attempt} attempts.") from e

            except (httpx.ConnectError, httpx.NetworkError) as e:
                last_exception = e
                if attempt < max_attempts:
                    delay = self.config.backoff_factor * (2 ** (attempt - 1))
                    await asyncio.sleep(min(delay, 5.0))
                    continue
                raise Channel3NetworkError(f"Channel3 network connection failed after {attempt} attempts: {e}") from e

            except (Channel3AuthError, Channel3BadRequestError, Channel3NotFoundError):
                # Non-retryable errors must not be retried
                raise

        # Fallback if loop exits without explicit return or raise
        if last_exception:
            raise Channel3NetworkError(f"Request failed: {last_exception}") from last_exception
        raise Channel3Error(f"Request to '{path}' failed after {max_attempts} attempts.")
