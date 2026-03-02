"""Tests for webhook signature verification."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from stripewrap.exceptions import SignatureVerificationError
from stripewrap.webhooks import construct_event, verify_header

WEBHOOK_SECRET = "whsec_test_secret_for_testing"
SIGNING_KEY = WEBHOOK_SECRET.removeprefix("whsec_")

SAMPLE_PAYLOAD = json.dumps(
    {
        "id": "evt_test_webhook",
        "object": "event",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_test_123"}},
    }
)


def _make_sig_header(payload: str, secret: str, timestamp: int | None = None) -> str:
    """Build a valid Stripe-Signature header for testing."""
    ts = timestamp or int(time.time())
    signed = f"{ts}.{payload}"
    sig = hmac.HMAC(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


class TestVerifyHeader:
    def test_valid_signature(self):
        """A correctly signed webhook should pass without error."""
        header = _make_sig_header(SAMPLE_PAYLOAD, SIGNING_KEY)
        verify_header(SAMPLE_PAYLOAD, header, WEBHOOK_SECRET)  # should not raise

    def test_valid_bytes_payload(self):
        header = _make_sig_header(SAMPLE_PAYLOAD, SIGNING_KEY)
        verify_header(SAMPLE_PAYLOAD.encode(), header, WEBHOOK_SECRET)  # bytes payload

    def test_tampered_payload(self):
        """Modified payload should fail signature check."""
        header = _make_sig_header(SAMPLE_PAYLOAD, SIGNING_KEY)
        tampered = SAMPLE_PAYLOAD + " extra"
        with pytest.raises(SignatureVerificationError, match="Signature mismatch"):
            verify_header(tampered, header, WEBHOOK_SECRET)

    def test_wrong_secret(self):
        """Signature computed with different secret should fail."""
        header = _make_sig_header(SAMPLE_PAYLOAD, "wrong_secret")
        with pytest.raises(SignatureVerificationError, match="Signature mismatch"):
            verify_header(SAMPLE_PAYLOAD, header, WEBHOOK_SECRET)

    def test_expired_timestamp(self):
        """Timestamps older than tolerance should be rejected."""
        old_ts = int(time.time()) - 400  # older than default 300s tolerance
        header = _make_sig_header(SAMPLE_PAYLOAD, SIGNING_KEY, timestamp=old_ts)
        with pytest.raises(SignatureVerificationError, match="too old"):
            verify_header(SAMPLE_PAYLOAD, header, WEBHOOK_SECRET)

    def test_disable_tolerance(self):
        """Setting tolerance=None disables timestamp validation."""
        old_ts = int(time.time()) - 10000
        header = _make_sig_header(SAMPLE_PAYLOAD, SIGNING_KEY, timestamp=old_ts)
        verify_header(SAMPLE_PAYLOAD, header, WEBHOOK_SECRET, tolerance=None)

    def test_malformed_header(self):
        """Completely invalid header should raise SignatureVerificationError."""
        with pytest.raises(SignatureVerificationError, match="Unable to parse"):
            verify_header(SAMPLE_PAYLOAD, "not_a_valid=header_format", WEBHOOK_SECRET)

    def test_missing_v1_signature(self):
        """Header with timestamp but no v1 signature."""
        ts = int(time.time())
        with pytest.raises(SignatureVerificationError, match="No v1 signatures"):
            verify_header(SAMPLE_PAYLOAD, f"t={ts}", WEBHOOK_SECRET)


class TestConstructEvent:
    def test_construct_event_success(self):
        """Valid payload should be parsed and returned as a dict."""
        header = _make_sig_header(SAMPLE_PAYLOAD, SIGNING_KEY)
        event = construct_event(SAMPLE_PAYLOAD, header, WEBHOOK_SECRET)

        assert event["id"] == "evt_test_webhook"
        assert event["type"] == "payment_intent.succeeded"

    def test_construct_event_invalid_signature(self):
        """Invalid signature should propagate as SignatureVerificationError."""
        header = _make_sig_header(SAMPLE_PAYLOAD, "wrong_key")
        with pytest.raises(SignatureVerificationError):
            construct_event(SAMPLE_PAYLOAD, header, WEBHOOK_SECRET)
