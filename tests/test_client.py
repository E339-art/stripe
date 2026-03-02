"""Tests for the synchronous StripeClient."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from stripewrap import AuthenticationError, CardError, InvalidRequestError, StripeClient
from stripewrap.models import Customer, PaymentIntent

BASE_URL = "https://api.stripe.com/v1"


class TestPaymentIntents:
    def test_create_payment_intent(self, client: StripeClient, payment_intent_payload: dict):
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(200, json=payment_intent_payload)
            )
            intent = client.payment_intents.create(amount=2000, currency="usd")

        assert isinstance(intent, PaymentIntent)
        assert intent.id == "pi_test_123"
        assert intent.amount == 2000
        assert intent.currency == "usd"
        assert intent.status == "requires_payment_method"

    def test_retrieve_payment_intent(self, client: StripeClient, payment_intent_payload: dict):
        with respx.mock:
            respx.get(f"{BASE_URL}/payment_intents/pi_test_123").mock(
                return_value=Response(200, json=payment_intent_payload)
            )
            intent = client.payment_intents.retrieve("pi_test_123")

        assert intent.id == "pi_test_123"

    def test_update_payment_intent(self, client: StripeClient, payment_intent_payload: dict):
        updated = {**payment_intent_payload, "description": "Updated"}
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents/pi_test_123").mock(
                return_value=Response(200, json=updated)
            )
            intent = client.payment_intents.update("pi_test_123", description="Updated")

        assert intent.id == "pi_test_123"

    def test_list_payment_intents(self, client: StripeClient, payment_intent_payload: dict):
        list_payload = {
            "object": "list",
            "data": [payment_intent_payload],
            "has_more": False,
            "url": "/v1/payment_intents",
        }
        with respx.mock:
            respx.get(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(200, json=list_payload)
            )
            result = client.payment_intents.list(limit=10)

        assert len(result.data) == 1
        assert result.data[0].id == "pi_test_123"
        assert not result.has_more

    def test_list_auto_paging(self, client: StripeClient, payment_intent_payload: dict):
        """Auto-pagination should follow has_more / starting_after."""
        pi2 = {**payment_intent_payload, "id": "pi_test_456"}
        page1 = {
            "object": "list",
            "data": [payment_intent_payload],
            "has_more": True,
            "url": "/v1/payment_intents",
        }
        page2 = {
            "object": "list",
            "data": [pi2],
            "has_more": False,
            "url": "/v1/payment_intents",
        }

        with respx.mock:
            route = respx.get(f"{BASE_URL}/payment_intents")
            route.side_effect = [
                Response(200, json=page1),
                Response(200, json=page2),
            ]
            items = list(client.payment_intents.list_auto_paging())

        assert len(items) == 2
        assert items[0].id == "pi_test_123"
        assert items[1].id == "pi_test_456"


class TestCustomers:
    def test_create_customer(self, client: StripeClient, customer_payload: dict):
        with respx.mock:
            respx.post(f"{BASE_URL}/customers").mock(
                return_value=Response(200, json=customer_payload)
            )
            customer = client.customers.create(email="test@example.com", name="Test User")

        assert isinstance(customer, Customer)
        assert customer.id == "cus_test_abc"
        assert customer.email == "test@example.com"

    def test_retrieve_customer(self, client: StripeClient, customer_payload: dict):
        with respx.mock:
            respx.get(f"{BASE_URL}/customers/cus_test_abc").mock(
                return_value=Response(200, json=customer_payload)
            )
            customer = client.customers.retrieve("cus_test_abc")

        assert customer.name == "Test User"

    def test_delete_customer(self, client: StripeClient):
        deleted_payload = {"id": "cus_test_abc", "object": "customer", "deleted": True}
        with respx.mock:
            respx.delete(f"{BASE_URL}/customers/cus_test_abc").mock(
                return_value=Response(200, json=deleted_payload)
            )
            result = client.customers.delete("cus_test_abc")

        assert result.deleted is True
        assert result.id == "cus_test_abc"


class TestErrorHandling:
    def test_authentication_error(self, client: StripeClient, error_401_payload: dict):
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(401, json=error_401_payload)
            )
            with pytest.raises(AuthenticationError) as exc_info:
                client.payment_intents.create(amount=2000, currency="usd")

        assert exc_info.value.http_status == 401

    def test_card_error(self, client: StripeClient, error_402_payload: dict):
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(402, json=error_402_payload)
            )
            with pytest.raises(CardError) as exc_info:
                client.payment_intents.create(amount=2000, currency="usd")

        err = exc_info.value
        assert err.http_status == 402
        assert err.decline_code == "insufficient_funds"
        assert err.charge == "ch_test_declined"

    def test_invalid_request_error(self, client: StripeClient):
        payload = {
            "error": {
                "type": "invalid_request_error",
                "message": "amount must be greater than 0",
                "param": "amount",
            }
        }
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(400, json=payload)
            )
            with pytest.raises(InvalidRequestError) as exc_info:
                client.payment_intents.create(amount=-1, currency="usd")

        assert exc_info.value.param == "amount"


class TestContextManager:
    def test_sync_context_manager(self, payment_intent_payload: dict):
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(200, json=payment_intent_payload)
            )
            with StripeClient("sk_test_ctx", max_retries=0) as client:
                intent = client.payment_intents.create(amount=2000, currency="usd")

        assert intent.id == "pi_test_123"
