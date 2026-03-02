"""Synchronous Stripe API client."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import httpx

logger = logging.getLogger(__name__)

from stripewrap.exceptions import APIConnectionError, _raise_for_response
from stripewrap.models import (
    Charge,
    Customer,
    DeletedObject,
    Invoice,
    ListResponse,
    PaymentIntent,
    PaymentMethod,
    Refund,
    Subscription,
)
from stripewrap.pagination import auto_paging_iter
from stripewrap.retry import RETRYABLE_STATUS_CODES, retry_sync

_BASE_URL = "https://api.stripe.com/v1"
_DEFAULT_TIMEOUT = 30.0


class _Resource:
    def __init__(self, client: StripeClient) -> None:
        self._client = client

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._client._request(method, path, params=params, data=data)


class PaymentIntents(_Resource):
    """Manage Stripe PaymentIntents."""

    def create(
        self,
        *,
        amount: int,
        currency: str,
        **kwargs: Any,
    ) -> PaymentIntent:
        """Create a new PaymentIntent."""
        data = {"amount": amount, "currency": currency, **kwargs}
        return PaymentIntent.model_validate(self._request("POST", "/payment_intents", data=data))

    def retrieve(self, payment_intent_id: str) -> PaymentIntent:
        """Retrieve a PaymentIntent by ID."""
        return PaymentIntent.model_validate(
            self._request("GET", f"/payment_intents/{payment_intent_id}")
        )

    def update(self, payment_intent_id: str, **kwargs: Any) -> PaymentIntent:
        """Update a PaymentIntent."""
        return PaymentIntent.model_validate(
            self._request("POST", f"/payment_intents/{payment_intent_id}", data=kwargs)
        )

    def confirm(self, payment_intent_id: str, **kwargs: Any) -> PaymentIntent:
        """Confirm a PaymentIntent."""
        return PaymentIntent.model_validate(
            self._request("POST", f"/payment_intents/{payment_intent_id}/confirm", data=kwargs)
        )

    def cancel(self, payment_intent_id: str, **kwargs: Any) -> PaymentIntent:
        """Cancel a PaymentIntent."""
        return PaymentIntent.model_validate(
            self._request("POST", f"/payment_intents/{payment_intent_id}/cancel", data=kwargs)
        )

    def list(self, **kwargs: Any) -> ListResponse[PaymentIntent]:
        """List PaymentIntents."""
        raw = self._request("GET", "/payment_intents", params=kwargs)
        return ListResponse[PaymentIntent].model_validate(raw)

    def list_auto_paging(self, **kwargs: Any) -> Iterator[PaymentIntent]:
        """Iterate over all PaymentIntents, fetching additional pages automatically."""
        yield from auto_paging_iter(self.list, **kwargs)


class Customers(_Resource):
    """Manage Stripe Customers."""

    def create(self, **kwargs: Any) -> Customer:
        """Create a new Customer."""
        return Customer.model_validate(self._request("POST", "/customers", data=kwargs))

    def retrieve(self, customer_id: str) -> Customer:
        """Retrieve a Customer by ID."""
        return Customer.model_validate(self._request("GET", f"/customers/{customer_id}"))

    def update(self, customer_id: str, **kwargs: Any) -> Customer:
        """Update a Customer."""
        return Customer.model_validate(
            self._request("POST", f"/customers/{customer_id}", data=kwargs)
        )

    def delete(self, customer_id: str) -> DeletedObject:
        """Delete a Customer."""
        return DeletedObject.model_validate(self._request("DELETE", f"/customers/{customer_id}"))

    def list(self, **kwargs: Any) -> ListResponse[Customer]:
        """List Customers."""
        raw = self._request("GET", "/customers", params=kwargs)
        return ListResponse[Customer].model_validate(raw)

    def list_auto_paging(self, **kwargs: Any) -> Iterator[Customer]:
        """Iterate over all Customers, fetching additional pages automatically."""
        yield from auto_paging_iter(self.list, **kwargs)


class Charges(_Resource):
    """Manage Stripe Charges."""

    def create(self, *, amount: int, currency: str, **kwargs: Any) -> Charge:
        """Create a new Charge."""
        data = {"amount": amount, "currency": currency, **kwargs}
        return Charge.model_validate(self._request("POST", "/charges", data=data))

    def retrieve(self, charge_id: str) -> Charge:
        """Retrieve a Charge by ID."""
        return Charge.model_validate(self._request("GET", f"/charges/{charge_id}"))

    def update(self, charge_id: str, **kwargs: Any) -> Charge:
        """Update a Charge."""
        return Charge.model_validate(
            self._request("POST", f"/charges/{charge_id}", data=kwargs)
        )

    def list(self, **kwargs: Any) -> ListResponse[Charge]:
        """List Charges."""
        raw = self._request("GET", "/charges", params=kwargs)
        return ListResponse[Charge].model_validate(raw)

    def list_auto_paging(self, **kwargs: Any) -> Iterator[Charge]:
        """Iterate over all Charges, fetching additional pages automatically."""
        yield from auto_paging_iter(self.list, **kwargs)


class Refunds(_Resource):
    """Manage Stripe Refunds."""

    def create(self, *, charge: str | None = None, payment_intent: str | None = None, **kwargs: Any) -> Refund:
        """Create a Refund."""
        data: dict[str, Any] = {**kwargs}
        if charge:
            data["charge"] = charge
        if payment_intent:
            data["payment_intent"] = payment_intent
        return Refund.model_validate(self._request("POST", "/refunds", data=data))

    def retrieve(self, refund_id: str) -> Refund:
        """Retrieve a Refund."""
        return Refund.model_validate(self._request("GET", f"/refunds/{refund_id}"))

    def list(self, **kwargs: Any) -> ListResponse[Refund]:
        """List Refunds."""
        raw = self._request("GET", "/refunds", params=kwargs)
        return ListResponse[Refund].model_validate(raw)

    def list_auto_paging(self, **kwargs: Any) -> Iterator[Refund]:
        """Iterate over all Refunds automatically."""
        yield from auto_paging_iter(self.list, **kwargs)


class PaymentMethods(_Resource):
    """Manage Stripe PaymentMethods."""

    def retrieve(self, payment_method_id: str) -> PaymentMethod:
        """Retrieve a PaymentMethod."""
        return PaymentMethod.model_validate(
            self._request("GET", f"/payment_methods/{payment_method_id}")
        )

    def list(self, *, customer: str, type: str = "card", **kwargs: Any) -> ListResponse[PaymentMethod]:
        """List PaymentMethods for a customer."""
        raw = self._request("GET", "/payment_methods", params={"customer": customer, "type": type, **kwargs})
        return ListResponse[PaymentMethod].model_validate(raw)


class Subscriptions(_Resource):
    """Manage Stripe Subscriptions."""

    def create(self, *, customer: str, items: list[dict[str, Any]], **kwargs: Any) -> Subscription:
        """Create a Subscription."""
        data = {"customer": customer, "items": items, **kwargs}
        return Subscription.model_validate(self._request("POST", "/subscriptions", data=data))

    def retrieve(self, subscription_id: str) -> Subscription:
        """Retrieve a Subscription."""
        return Subscription.model_validate(
            self._request("GET", f"/subscriptions/{subscription_id}")
        )

    def update(self, subscription_id: str, **kwargs: Any) -> Subscription:
        """Update a Subscription."""
        return Subscription.model_validate(
            self._request("POST", f"/subscriptions/{subscription_id}", data=kwargs)
        )

    def cancel(self, subscription_id: str) -> Subscription:
        """Cancel a Subscription immediately."""
        return Subscription.model_validate(
            self._request("DELETE", f"/subscriptions/{subscription_id}")
        )

    def list(self, **kwargs: Any) -> ListResponse[Subscription]:
        """List Subscriptions."""
        raw = self._request("GET", "/subscriptions", params=kwargs)
        return ListResponse[Subscription].model_validate(raw)

    def list_auto_paging(self, **kwargs: Any) -> Iterator[Subscription]:
        """Iterate over all Subscriptions automatically."""
        yield from auto_paging_iter(self.list, **kwargs)


class Invoices(_Resource):
    """Manage Stripe Invoices."""

    def retrieve(self, invoice_id: str) -> Invoice:
        """Retrieve an Invoice."""
        return Invoice.model_validate(self._request("GET", f"/invoices/{invoice_id}"))

    def list(self, **kwargs: Any) -> ListResponse[Invoice]:
        """List Invoices."""
        raw = self._request("GET", "/invoices", params=kwargs)
        return ListResponse[Invoice].model_validate(raw)

    def list_auto_paging(self, **kwargs: Any) -> Iterator[Invoice]:
        """Iterate over all Invoices automatically."""
        yield from auto_paging_iter(self.list, **kwargs)


class StripeClient:
    """Synchronous Stripe API client.

    Args:
        api_key: Your Stripe secret key (starts with ``sk_``).
        timeout: HTTP request timeout in seconds (default: 30).
        max_retries: Maximum number of retry attempts for retryable errors
            (default: 2).
        base_url: Override the Stripe API base URL (useful for testing).

    Example::

        import stripewrap

        client = stripewrap.StripeClient("sk_test_...")

        intent = client.payment_intents.create(
            amount=2000,
            currency="usd",
        )
        print(intent.id, intent.status)
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = 2,
        base_url: str = _BASE_URL,
    ) -> None:
        self._api_key = api_key
        self._max_retries = max_retries
        self._base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Stripe-Version": "2024-06-20",
                "User-Agent": "stripewrap/0.1.0 python-httpx",
            },
        )

        # Resource namespaces
        self.payment_intents = PaymentIntents(self)
        self.customers = Customers(self)
        self.charges = Charges(self)
        self.refunds = Refunds(self)
        self.payment_methods = PaymentMethods(self)
        self.subscriptions = Subscriptions(self)
        self.invoices = Invoices(self)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"

        def _do_request() -> dict[str, Any]:
            try:
                response = self._http.request(
                    method,
                    url,
                    params=params,
                    data=data,
                )
            except httpx.ConnectError as exc:
                raise APIConnectionError(f"Failed to connect to Stripe API: {exc}") from exc
            except httpx.TimeoutException as exc:
                raise APIConnectionError(f"Request to Stripe API timed out: {exc}") from exc

            request_id = response.headers.get("request-id")
            json_body: dict[str, Any] = response.json()

            if response.status_code >= 400:
                logger.debug(
                    "Stripe API error: %s %s -> %d",
                    method,
                    path,
                    response.status_code,
                )
                _raise_for_response(response.status_code, json_body, request_id)

            logger.debug("Stripe API: %s %s -> %d", method, path, response.status_code)
            return json_body

        return retry_sync(  # type: ignore[return-value]
            _do_request,
            max_retries=self._max_retries,
            retryable_status_codes=RETRYABLE_STATUS_CODES,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> StripeClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
