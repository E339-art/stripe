"""Stripe exception hierarchy.

All exceptions raised by stripewrap inherit from :class:`StripeError`,
making it easy to catch all library errors with a single except clause
while still being able to handle specific error types precisely.
"""

from __future__ import annotations

from typing import Any


class StripeError(Exception):
    """Base class for all stripewrap exceptions."""

    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        request_id: str | None = None,
        code: str | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.request_id = request_id
        self.code = code
        self.json_body = json_body

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(message={self.message!r}, "
            f"http_status={self.http_status}, request_id={self.request_id!r})"
        )


class AuthenticationError(StripeError):
    """Raised when the API key is missing, invalid, or expired (HTTP 401)."""


class PermissionError(StripeError):
    """Raised when the API key doesn't have permission for the requested resource (HTTP 403)."""


class InvalidRequestError(StripeError):
    """Raised when request parameters are invalid (HTTP 400).

    The ``param`` attribute indicates which parameter caused the error,
    if Stripe was able to identify it.
    """

    def __init__(self, message: str, *, param: str | None = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.param = param


class NotFoundError(StripeError):
    """Raised when the requested resource does not exist (HTTP 404)."""


class CardError(StripeError):
    """Raised when a card operation fails.

    Attributes:
        code: A short string describing the error (e.g. ``"card_declined"``).
        decline_code: The decline code returned by the card network, if any.
        param: The parameter that caused the error, if applicable.
        charge: The ID of the failed charge, if a charge was created.
    """

    def __init__(
        self,
        message: str,
        *,
        decline_code: str | None = None,
        param: str | None = None,
        charge: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.decline_code = decline_code
        self.param = param
        self.charge = charge


class RateLimitError(StripeError):
    """Raised when too many requests are made in a short period (HTTP 429).

    Back off and retry after a short delay.
    """


class APIConnectionError(StripeError):
    """Raised when the SDK cannot connect to the Stripe API.

    This typically indicates a network problem, not an application error.
    """

    def __init__(self, message: str, *, should_retry: bool = True, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.should_retry = should_retry


class APIError(StripeError):
    """Raised for unexpected Stripe server errors (HTTP 500/502/503/504)."""


class IdempotencyError(StripeError):
    """Raised when an idempotency key is reused with different request parameters."""


class SignatureVerificationError(StripeError):
    """Raised when a webhook signature cannot be verified."""

    def __init__(self, message: str, *, sig_header: str | None = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.sig_header = sig_header


def _raise_for_response(
    status_code: int,
    json_body: dict[str, Any],
    request_id: str | None = None,
) -> None:
    """Parse a Stripe error response and raise the appropriate exception."""
    error = json_body.get("error", {})
    message = error.get("message", "An unknown error occurred")
    code = error.get("code")
    error_type = error.get("type", "")

    kwargs: dict[str, Any] = {
        "http_status": status_code,
        "request_id": request_id,
        "code": code,
        "json_body": json_body,
    }

    if status_code == 400:
        if error_type == "idempotency_error":
            raise IdempotencyError(message, **kwargs)
        raise InvalidRequestError(message, param=error.get("param"), **kwargs)
    elif status_code == 401:
        raise AuthenticationError(message, **kwargs)
    elif status_code == 402:
        raise CardError(
            message,
            decline_code=error.get("decline_code"),
            param=error.get("param"),
            charge=error.get("charge"),
            **kwargs,
        )
    elif status_code == 403:
        raise PermissionError(message, **kwargs)
    elif status_code == 404:
        raise NotFoundError(message, **kwargs)
    elif status_code == 429:
        raise RateLimitError(message, **kwargs)
    else:
        raise APIError(message, **kwargs)
