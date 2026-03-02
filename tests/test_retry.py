"""Tests for retry logic with exponential backoff."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from stripewrap.exceptions import APIConnectionError, APIError, RateLimitError
from stripewrap.retry import RETRYABLE_STATUS_CODES, compute_backoff, retry_sync


class TestComputeBackoff:
    def test_first_attempt_bounded(self):
        """First attempt backoff should be between 0 and base."""
        for _ in range(100):
            delay = compute_backoff(0, base=0.5)
            assert 0 <= delay <= 0.5

    def test_exponential_growth(self):
        """Ceiling should grow exponentially."""
        # attempt 0: ceiling = 0.5
        # attempt 1: ceiling = 1.0
        # attempt 2: ceiling = 2.0
        for _ in range(100):
            d0 = compute_backoff(0, base=0.5)
            d2 = compute_backoff(2, base=0.5)
            # d2 can be up to 2.0, d0 up to 0.5
            assert d0 <= 0.5
            assert d2 <= 2.0

    def test_max_wait_cap(self):
        """Backoff should never exceed max_wait."""
        for _ in range(100):
            delay = compute_backoff(100, base=0.5, max_wait=5.0)
            assert delay <= 5.0

    def test_zero_base(self):
        """Zero base should always return 0."""
        assert compute_backoff(0, base=0.0) == 0.0


class TestRetrySyncSuccess:
    @patch("stripewrap.retry.compute_backoff", return_value=0)
    @patch("stripewrap.retry.time.sleep")
    def test_succeeds_on_first_try(self, mock_sleep, mock_backoff):
        result = retry_sync(lambda: "ok", max_retries=2)
        assert result == "ok"
        mock_sleep.assert_not_called()

    @patch("stripewrap.retry.compute_backoff", return_value=0)
    @patch("stripewrap.retry.time.sleep")
    def test_succeeds_after_retry(self, mock_sleep, mock_backoff):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise APIConnectionError("Network error")
            return "recovered"

        result = retry_sync(flaky, max_retries=3)
        assert result == "recovered"
        assert call_count == 2
        assert mock_sleep.call_count == 1


class TestRetrySyncFailure:
    @patch("stripewrap.retry.compute_backoff", return_value=0)
    @patch("stripewrap.retry.time.sleep")
    def test_exhausts_retries(self, mock_sleep, mock_backoff):
        def always_fail():
            raise RateLimitError("Too many requests", http_status=429)

        with pytest.raises(RateLimitError):
            retry_sync(always_fail, max_retries=2)
        # Should have tried 3 times total (1 initial + 2 retries)
        assert mock_sleep.call_count == 2

    @patch("stripewrap.retry.compute_backoff", return_value=0)
    @patch("stripewrap.retry.time.sleep")
    def test_non_retryable_status_raises_immediately(self, mock_sleep, mock_backoff):
        """APIError with non-retryable status should not be retried."""
        def fail_with_400():
            raise APIError("Bad request", http_status=400)

        with pytest.raises(APIError):
            retry_sync(fail_with_400, max_retries=3)
        mock_sleep.assert_not_called()

    @patch("stripewrap.retry.compute_backoff", return_value=0)
    @patch("stripewrap.retry.time.sleep")
    def test_on_retry_callback(self, mock_sleep, mock_backoff):
        """on_retry callback should be invoked before each retry."""
        attempts = []

        def on_retry(attempt, exc):
            attempts.append(attempt)

        def always_fail():
            raise APIConnectionError("Down")

        with pytest.raises(APIConnectionError):
            retry_sync(always_fail, max_retries=2, on_retry=on_retry)

        assert attempts == [1, 2]


class TestRetryableStatusCodes:
    def test_expected_codes(self):
        assert 429 in RETRYABLE_STATUS_CODES
        assert 500 in RETRYABLE_STATUS_CODES
        assert 502 in RETRYABLE_STATUS_CODES
        assert 503 in RETRYABLE_STATUS_CODES
        assert 504 in RETRYABLE_STATUS_CODES
        assert 400 not in RETRYABLE_STATUS_CODES
        assert 401 not in RETRYABLE_STATUS_CODES
