"""Tests for the exception hierarchy."""

from __future__ import annotations

import pytest

from stripewrap.exceptions import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    CardError,
    IdempotencyError,
    InvalidRequestError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    SignatureVerificationError,
    StripeError,
    _raise_for_response,
)


class TestExceptionHierarchy:
    """All specific exceptions should inherit from StripeError."""

    @pytest.mark.parametrize(
        "exc_class",
        [
            AuthenticationError,
            PermissionError,
            InvalidRequestError,
            NotFoundError,
            CardError,
            RateLimitError,
            APIConnectionError,
            APIError,
            IdempotencyError,
            SignatureVerificationError,
        ],
    )
    def test_inherits_from_stripe_error(self, exc_class):
        assert issubclass(exc_class, StripeError)

    def test_stripe_error_attributes(self):
        err = StripeError(
            "test message",
            http_status=400,
            request_id="req_123",
            code="invalid_param",
            json_body={"error": {"message": "test"}},
        )
        assert err.message == "test message"
        assert err.http_status == 400
        assert err.request_id == "req_123"
        assert err.code == "invalid_param"
        assert str(err) == "test message"

    def test_stripe_error_repr(self):
        err = StripeError("oops", http_status=500, request_id="req_abc")
        r = repr(err)
        assert "StripeError" in r
        assert "oops" in r
        assert "500" in r

    def test_card_error_attributes(self):
        err = CardError(
            "Your card was declined",
            decline_code="insufficient_funds",
            param="number",
            charge="ch_test_123",
            http_status=402,
        )
        assert err.decline_code == "insufficient_funds"
        assert err.param == "number"
        assert err.charge == "ch_test_123"
        assert err.http_status == 402

    def test_invalid_request_error_param(self):
        err = InvalidRequestError(
            "Invalid amount", param="amount", http_status=400
        )
        assert err.param == "amount"

    def test_api_connection_error_should_retry(self):
        err = APIConnectionError("Network error", should_retry=True)
        assert err.should_retry is True

    def test_signature_verification_error_sig_header(self):
        err = SignatureVerificationError(
            "Bad signature", sig_header="t=123,v1=abc"
        )
        assert err.sig_header == "t=123,v1=abc"


class TestRaiseForResponse:
    """Test the _raise_for_response helper."""

    def test_400_invalid_request(self):
        body = {"error": {"type": "invalid_request_error", "message": "Bad param", "param": "amount"}}
        with pytest.raises(InvalidRequestError) as exc_info:
            _raise_for_response(400, body, "req_123")
        assert exc_info.value.param == "amount"
        assert exc_info.value.request_id == "req_123"

    def test_400_idempotency_error(self):
        body = {"error": {"type": "idempotency_error", "message": "Key reused"}}
        with pytest.raises(IdempotencyError):
            _raise_for_response(400, body, None)

    def test_401_authentication_error(self):
        body = {"error": {"type": "invalid_request_error", "message": "Bad key"}}
        with pytest.raises(AuthenticationError):
            _raise_for_response(401, body, None)

    def test_402_card_error(self):
        body = {
            "error": {
                "type": "card_error",
                "message": "Declined",
                "code": "card_declined",
                "decline_code": "insufficient_funds",
                "charge": "ch_test",
            }
        }
        with pytest.raises(CardError) as exc_info:
            _raise_for_response(402, body, None)
        assert exc_info.value.decline_code == "insufficient_funds"
        assert exc_info.value.charge == "ch_test"

    def test_403_permission_error(self):
        body = {"error": {"message": "Forbidden"}}
        with pytest.raises(PermissionError):
            _raise_for_response(403, body, None)

    def test_404_not_found_error(self):
        body = {"error": {"message": "Not found"}}
        with pytest.raises(NotFoundError):
            _raise_for_response(404, body, None)

    def test_429_rate_limit_error(self):
        body = {"error": {"message": "Rate limited"}}
        with pytest.raises(RateLimitError):
            _raise_for_response(429, body, None)

    def test_500_api_error(self):
        body = {"error": {"message": "Server error"}}
        with pytest.raises(APIError):
            _raise_for_response(500, body, None)

    def test_unknown_status_raises_api_error(self):
        body = {"error": {"message": "Unknown"}}
        with pytest.raises(APIError):
            _raise_for_response(599, body, None)

    def test_missing_error_body(self):
        """Should handle missing error key gracefully."""
        with pytest.raises(StripeError):
            _raise_for_response(500, {}, None)
