"""Tests for Pydantic v2 models."""

from __future__ import annotations

import pytest

from stripewrap.models import (
    Charge,
    Customer,
    DeletedObject,
    Event,
    EventData,
    Invoice,
    ListResponse,
    PaymentIntent,
    PaymentMethod,
    Refund,
    Subscription,
)


class TestCustomer:
    def test_basic_customer(self):
        data = {
            "id": "cus_test_123",
            "object": "customer",
            "created": 1700000000,
            "email": "test@example.com",
            "name": "Test User",
            "livemode": False,
        }
        customer = Customer.model_validate(data)
        assert customer.id == "cus_test_123"
        assert customer.email == "test@example.com"
        assert customer.name == "Test User"
        assert customer.metadata == {}

    def test_customer_repr(self):
        customer = Customer(
            id="cus_abc", created=1700000000, email="a@b.com"
        )
        assert "cus_abc" in repr(customer)
        assert "a@b.com" in repr(customer)

    def test_customer_extra_fields(self):
        """Extra fields from Stripe should not cause validation errors."""
        data = {
            "id": "cus_test",
            "object": "customer",
            "created": 1700000000,
            "livemode": False,
            "some_new_field": "should_not_fail",
        }
        customer = Customer.model_validate(data)
        assert customer.id == "cus_test"


class TestPaymentIntent:
    def test_basic_payment_intent(self):
        data = {
            "id": "pi_test_123",
            "object": "payment_intent",
            "amount": 2000,
            "currency": "usd",
            "status": "requires_payment_method",
            "created": 1700000000,
            "livemode": False,
        }
        intent = PaymentIntent.model_validate(data)
        assert intent.id == "pi_test_123"
        assert intent.amount == 2000
        assert intent.currency == "usd"

    def test_amount_in_major_units(self):
        intent = PaymentIntent(
            id="pi_test",
            amount=4999,
            currency="usd",
            status="succeeded",
            created=1700000000,
        )
        assert intent.amount_in_major_units == 49.99

    def test_payment_intent_repr(self):
        intent = PaymentIntent(
            id="pi_test",
            amount=2000,
            currency="usd",
            status="succeeded",
            created=1700000000,
        )
        r = repr(intent)
        assert "pi_test" in r
        assert "2000" in r
        assert "usd" in r
        assert "succeeded" in r


class TestCharge:
    def test_basic_charge(self):
        data = {
            "id": "ch_test_xyz",
            "object": "charge",
            "amount": 2000,
            "currency": "usd",
            "created": 1700000000,
            "status": "succeeded",
            "paid": True,
            "captured": True,
        }
        charge = Charge.model_validate(data)
        assert charge.id == "ch_test_xyz"
        assert charge.paid is True
        assert charge.captured is True

    def test_charge_repr(self):
        charge = Charge(
            id="ch_test",
            amount=5000,
            currency="eur",
            created=1700000000,
            status="pending",
        )
        assert "ch_test" in repr(charge)


class TestRefund:
    def test_basic_refund(self):
        data = {
            "id": "re_test_123",
            "object": "refund",
            "amount": 1000,
            "currency": "usd",
            "created": 1700000000,
            "status": "succeeded",
        }
        refund = Refund.model_validate(data)
        assert refund.id == "re_test_123"
        assert refund.amount == 1000


class TestListResponse:
    def test_list_response(self):
        data = {
            "object": "list",
            "data": [
                {
                    "id": "cus_1",
                    "object": "customer",
                    "created": 1700000000,
                    "livemode": False,
                },
                {
                    "id": "cus_2",
                    "object": "customer",
                    "created": 1700000001,
                    "livemode": False,
                },
            ],
            "has_more": True,
            "url": "/v1/customers",
        }
        result = ListResponse[Customer].model_validate(data)
        assert len(result.data) == 2
        assert result.has_more is True
        assert result.data[0].id == "cus_1"

    def test_list_response_repr(self):
        result = ListResponse[Customer](
            data=[], has_more=False, url="/v1/customers"
        )
        assert "count=0" in repr(result)
        assert "has_more=False" in repr(result)


class TestEvent:
    def test_basic_event(self):
        data = {
            "id": "evt_test_123",
            "object": "event",
            "api_version": "2024-06-20",
            "created": 1700000000,
            "data": {
                "object": {"id": "pi_test_123", "amount": 2000},
            },
            "livemode": False,
            "pending_webhooks": 1,
            "type": "payment_intent.succeeded",
        }
        event = Event.model_validate(data)
        assert event.id == "evt_test_123"
        assert event.type == "payment_intent.succeeded"
        assert event.data.object["id"] == "pi_test_123"

    def test_event_repr(self):
        event = Event(
            id="evt_test",
            created=1700000000,
            data=EventData(object={"id": "pi_test"}),
            type="charge.succeeded",
        )
        assert "evt_test" in repr(event)
        assert "charge.succeeded" in repr(event)


class TestDeletedObject:
    def test_deleted_object(self):
        data = {
            "id": "cus_deleted",
            "object": "customer",
            "deleted": True,
        }
        deleted = DeletedObject.model_validate(data)
        assert deleted.id == "cus_deleted"
        assert deleted.deleted is True

    def test_deleted_object_repr(self):
        deleted = DeletedObject(id="cus_x", object="customer")
        assert "cus_x" in repr(deleted)
