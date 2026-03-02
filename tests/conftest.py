"""Shared pytest fixtures for stripewrap tests."""

from __future__ import annotations

import pytest
import respx

from stripewrap import AsyncStripeClient, StripeClient

TEST_API_KEY = "sk_test_stripewrap_fixture"
BASE_URL = "https://api.stripe.com/v1"


@pytest.fixture
def client():
    """Sync StripeClient pointed at a mocked HTTPX transport."""
    with StripeClient(TEST_API_KEY, max_retries=0) as c:
        yield c


@pytest.fixture
async def async_client():
    """Async StripeClient pointed at a mocked HTTPX transport."""
    async with AsyncStripeClient(TEST_API_KEY, max_retries=0) as c:
        yield c


@pytest.fixture
def payment_intent_payload():
    return {
        "id": "pi_test_123",
        "object": "payment_intent",
        "amount": 2000,
        "currency": "usd",
        "status": "requires_payment_method",
        "created": 1700000000,
        "livemode": False,
        "payment_method_types": ["card"],
    }


@pytest.fixture
def customer_payload():
    return {
        "id": "cus_test_abc",
        "object": "customer",
        "created": 1700000000,
        "email": "test@example.com",
        "name": "Test User",
        "livemode": False,
    }


@pytest.fixture
def charge_payload():
    return {
        "id": "ch_test_xyz",
        "object": "charge",
        "amount": 2000,
        "currency": "usd",
        "created": 1700000000,
        "status": "succeeded",
        "paid": True,
        "captured": True,
    }


@pytest.fixture
def error_401_payload():
    return {
        "error": {
            "type": "invalid_request_error",
            "message": "No such API key: sk_test_bad",
            "code": "api_key_expired",
        }
    }


@pytest.fixture
def error_402_payload():
    return {
        "error": {
            "type": "card_error",
            "message": "Your card was declined.",
            "code": "card_declined",
            "decline_code": "insufficient_funds",
            "charge": "ch_test_declined",
        }
    }
