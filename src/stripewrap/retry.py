"""Retry logic with exponential backoff and jitter."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

F = TypeVar("F")

# HTTP status codes that are safe to retry
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def compute_backoff(attempt: int, base: float = 0.5, max_wait: float = 20.0) -> float:
    """Compute exponential backoff with full jitter.

    Args:
        attempt: Zero-indexed attempt number (0 = first retry).
        base: Base delay in seconds.
        max_wait: Maximum delay in seconds.

    Returns:
        Seconds to wait before the next attempt.
    """
    ceiling = min(base * (2**attempt), max_wait)
    return random.uniform(0, ceiling)


def retry_sync(
    func: Callable[[], F],
    *,
    max_retries: int = 2,
    retryable_status_codes: set[int] = RETRYABLE_STATUS_CODES,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> F:
    """Execute *func* and retry on retryable errors.

    Args:
        func: Zero-argument callable to execute.
        max_retries: Maximum number of retry attempts (not counting the initial call).
        retryable_status_codes: HTTP status codes that trigger a retry.
        on_retry: Optional callback invoked before each retry with
            ``(attempt_number, exception)``.

    Returns:
        The return value of *func* on success.

    Raises:
        The last exception raised by *func* after all retries are exhausted.
    """
    from stripewrap.exceptions import APIConnectionError, APIError, RateLimitError

    retryable_exceptions = (APIConnectionError, RateLimitError, APIError)

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except retryable_exceptions as exc:
            last_exc = exc
            # Don't retry if we've exhausted retries
            if attempt >= max_retries:
                break
            # For APIError, only retry on retryable status codes
            if isinstance(exc, APIError) and exc.http_status not in retryable_status_codes:
                raise
            if on_retry is not None:
                on_retry(attempt + 1, exc)
            time.sleep(compute_backoff(attempt))

    assert last_exc is not None
    raise last_exc


async def retry_async(
    func: Callable[[], object],
    *,
    max_retries: int = 2,
    retryable_status_codes: set[int] = RETRYABLE_STATUS_CODES,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> object:
    """Async version of :func:`retry_sync`."""
    import asyncio

    from stripewrap.exceptions import APIConnectionError, APIError, RateLimitError

    retryable_exceptions = (APIConnectionError, RateLimitError, APIError)

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await func()  # type: ignore[misc]
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt >= max_retries:
                break
            if isinstance(exc, APIError) and exc.http_status not in retryable_status_codes:
                raise
            if on_retry is not None:
                on_retry(attempt + 1, exc)
            await asyncio.sleep(compute_backoff(attempt))

    assert last_exc is not None
    raise last_exc
