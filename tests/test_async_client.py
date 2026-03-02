"""Tests for the asynchronous AsyncStripeClient."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from stripewrap import AsyncStripeClient, AuthenticationError, CardError
from stripewrap.models import Customer, PaymentIntent

BASE_URL = "https://api.stripe.com/v1"


class TestAsyncPaymentIntents:
    async def test_create_payment_intent(
        self, async_client: AsyncStripeClient, payment_intent_payload: dict
    ):
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(200, json=payment_intent_payload)
            )
            intent = await async_client.payment_intents.create(amount=2000, currency="usd")

        assert isinstance(intent, PaymentIntent)
        assert intent.id == "pi_test_123"
        assert intent.amount == 2000

    async def test_retrieve_payment_intent(
        self, async_client: AsyncStripeClient, payment_intent_payload: dict
    ):
        with respx.mock:
            respx.get(f"{BASE_URL}/payment_intents/pi_test_123").mock(
                return_value=Response(200, json=payment_intent_payload)
            )
            intent = await async_client.payment_intents.retrieve("pi_test_123")

        assert intent.id == "pi_test_123"

    async def test_list_auto_paging(
        self, async_client: AsyncStripeClient, payment_intent_payload: dict
    ):
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
            items = [item async for item in async_client.payment_intents.list_auto_paging()]

        assert len(items) == 2
        assert items[0].id == "pi_test_123"
        assert items[1].id == "pi_test_456"


class TestAsyncCustomers:
    async def test_create_customer(
        self, async_client: AsyncStripeClient, customer_payload: dict
    ):
        with respx.mock:
            respx.post(f"{BASE_URL}/customers").mock(
                return_value=Response(200, json=customer_payload)
            )
            customer = await async_client.customers.create(
                email="test@example.com", name="Test User"
            )

        assert isinstance(customer, Customer)
        assert customer.id == "cus_test_abc"

    async def test_update_customer(
        self, async_client: AsyncStripeClient, customer_payload: dict
    ):
        updated = {**customer_payload, "name": "Updated Name"}
        with respx.mock:
            respx.post(f"{BASE_URL}/customers/cus_test_abc").mock(
                return_value=Response(200, json=updated)
            )
            customer = await async_client.customers.update("cus_test_abc", name="Updated Name")

        assert customer.name == "Updated Name"


class TestAsyncErrorHandling:
    async def test_authentication_error(
        self, async_client: AsyncStripeClient, error_401_payload: dict
    ):
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(401, json=error_401_payload)
            )
            with pytest.raises(AuthenticationError) as exc_info:
                await async_client.payment_intents.create(amount=2000, currency="usd")

        assert exc_info.value.http_status == 401

    async def test_card_error(self, async_client: AsyncStripeClient, error_402_payload: dict):
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(402, json=error_402_payload)
            )
            with pytest.raises(CardError) as exc_info:
                await async_client.payment_intents.create(amount=2000, currency="usd")

        err = exc_info.value
        assert err.decline_code == "insufficient_funds"


class TestAsyncContextManager:
    async def test_async_context_manager(self, payment_intent_payload: dict):
        with respx.mock:
            respx.post(f"{BASE_URL}/payment_intents").mock(
                return_value=Response(200, json=payment_intent_payload)
            )
            async with AsyncStripeClient("sk_test_ctx", max_retries=0) as client:
                intent = await client.payment_intents.create(amount=2000, currency="usd")

        assert intent.id == "pi_test_123"
