"""Asynchronous Stripe API client.

The async client has an identical resource API to the sync
:class:`~stripewrap.client.StripeClient` — every method simply adds
``await`` and uses an async HTTP transport under the hood.

Example::

    import asyncio
    import stripewrap

    async def main():
        async with stripewrap.AsyncStripeClient("sk_test_...") as client:
            intent = await client.payment_intents.create(
                amount=2000,
                currency="usd",
            )
            print(intent.id, intent.status)

    asyncio.run(main())
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

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
from stripewrap.pagination import async_auto_paging_iter
from stripewrap.retry import RETRYABLE_STATUS_CODES, retry_async

_BASE_URL = "https://api.stripe.com/v1"
_DEFAULT_TIMEOUT = 30.0


class _AsyncResource:
    def __init__(self, client: AsyncStripeClient) -> None:
        self._client = client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._client._request(method, path, params=params, data=data)


class AsyncPaymentIntents(_AsyncResource):
    """Async PaymentIntents resource."""

    async def create(self, *, amount: int, currency: str, **kwargs: Any) -> PaymentIntent:
        data = {"amount": amount, "currency": currency, **kwargs}
        return PaymentIntent.model_validate(await self._request("POST", "/payment_intents", data=data))

    async def retrieve(self, payment_intent_id: str) -> PaymentIntent:
        return PaymentIntent.model_validate(
            await self._request("GET", f"/payment_intents/{payment_intent_id}")
        )

    async def update(self, payment_intent_id: str, **kwargs: Any) -> PaymentIntent:
        return PaymentIntent.model_validate(
            await self._request("POST", f"/payment_intents/{payment_intent_id}", data=kwargs)
        )

    async def confirm(self, payment_intent_id: str, **kwargs: Any) -> PaymentIntent:
        return PaymentIntent.model_validate(
            await self._request("POST", f"/payment_intents/{payment_intent_id}/confirm", data=kwargs)
        )

    async def cancel(self, payment_intent_id: str, **kwargs: Any) -> PaymentIntent:
        return PaymentIntent.model_validate(
            await self._request("POST", f"/payment_intents/{payment_intent_id}/cancel", data=kwargs)
        )

    async def list(self, **kwargs: Any) -> ListResponse[PaymentIntent]:
        raw = await self._request("GET", "/payment_intents", params=kwargs)
        return ListResponse[PaymentIntent].model_validate(raw)

    async def list_auto_paging(self, **kwargs: Any) -> AsyncIterator[PaymentIntent]:
        async for item in async_auto_paging_iter(self.list, **kwargs):
            yield item


class AsyncCustomers(_AsyncResource):
    """Async Customers resource."""

    async def create(self, **kwargs: Any) -> Customer:
        return Customer.model_validate(await self._request("POST", "/customers", data=kwargs))

    async def retrieve(self, customer_id: str) -> Customer:
        return Customer.model_validate(await self._request("GET", f"/customers/{customer_id}"))

    async def update(self, customer_id: str, **kwargs: Any) -> Customer:
        return Customer.model_validate(
            await self._request("POST", f"/customers/{customer_id}", data=kwargs)
        )

    async def delete(self, customer_id: str) -> DeletedObject:
        return DeletedObject.model_validate(
            await self._request("DELETE", f"/customers/{customer_id}")
        )

    async def list(self, **kwargs: Any) -> ListResponse[Customer]:
        raw = await self._request("GET", "/customers", params=kwargs)
        return ListResponse[Customer].model_validate(raw)

    async def list_auto_paging(self, **kwargs: Any) -> AsyncIterator[Customer]:
        async for item in async_auto_paging_iter(self.list, **kwargs):
            yield item


class AsyncCharges(_AsyncResource):
    """Async Charges resource."""

    async def create(self, *, amount: int, currency: str, **kwargs: Any) -> Charge:
        data = {"amount": amount, "currency": currency, **kwargs}
        return Charge.model_validate(await self._request("POST", "/charges", data=data))

    async def retrieve(self, charge_id: str) -> Charge:
        return Charge.model_validate(await self._request("GET", f"/charges/{charge_id}"))

    async def update(self, charge_id: str, **kwargs: Any) -> Charge:
        return Charge.model_validate(
            await self._request("POST", f"/charges/{charge_id}", data=kwargs)
        )

    async def list(self, **kwargs: Any) -> ListResponse[Charge]:
        raw = await self._request("GET", "/charges", params=kwargs)
        return ListResponse[Charge].model_validate(raw)

    async def list_auto_paging(self, **kwargs: Any) -> AsyncIterator[Charge]:
        async for item in async_auto_paging_iter(self.list, **kwargs):
            yield item


class AsyncRefunds(_AsyncResource):
    """Async Refunds resource."""

    async def create(
        self,
        *,
        charge: str | None = None,
        payment_intent: str | None = None,
        **kwargs: Any,
    ) -> Refund:
        data: dict[str, Any] = {**kwargs}
        if charge:
            data["charge"] = charge
        if payment_intent:
            data["payment_intent"] = payment_intent
        return Refund.model_validate(await self._request("POST", "/refunds", data=data))

    async def retrieve(self, refund_id: str) -> Refund:
        return Refund.model_validate(await self._request("GET", f"/refunds/{refund_id}"))

    async def list(self, **kwargs: Any) -> ListResponse[Refund]:
        raw = await self._request("GET", "/refunds", params=kwargs)
        return ListResponse[Refund].model_validate(raw)

    async def list_auto_paging(self, **kwargs: Any) -> AsyncIterator[Refund]:
        async for item in async_auto_paging_iter(self.list, **kwargs):
            yield item


class AsyncPaymentMethods(_AsyncResource):
    """Async PaymentMethods resource."""

    async def retrieve(self, payment_method_id: str) -> PaymentMethod:
        return PaymentMethod.model_validate(
            await self._request("GET", f"/payment_methods/{payment_method_id}")
        )

    async def list(self, *, customer: str, type: str = "card", **kwargs: Any) -> ListResponse[PaymentMethod]:
        raw = await self._request(
            "GET",
            "/payment_methods",
            params={"customer": customer, "type": type, **kwargs},
        )
        return ListResponse[PaymentMethod].model_validate(raw)


class AsyncSubscriptions(_AsyncResource):
    """Async Subscriptions resource."""

    async def create(self, *, customer: str, items: list[dict[str, Any]], **kwargs: Any) -> Subscription:
        data = {"customer": customer, "items": items, **kwargs}
        return Subscription.model_validate(await self._request("POST", "/subscriptions", data=data))

    async def retrieve(self, subscription_id: str) -> Subscription:
        return Subscription.model_validate(
            await self._request("GET", f"/subscriptions/{subscription_id}")
        )

    async def update(self, subscription_id: str, **kwargs: Any) -> Subscription:
        return Subscription.model_validate(
            await self._request("POST", f"/subscriptions/{subscription_id}", data=kwargs)
        )

    async def cancel(self, subscription_id: str) -> Subscription:
        return Subscription.model_validate(
            await self._request("DELETE", f"/subscriptions/{subscription_id}")
        )

    async def list(self, **kwargs: Any) -> ListResponse[Subscription]:
        raw = await self._request("GET", "/subscriptions", params=kwargs)
        return ListResponse[Subscription].model_validate(raw)

    async def list_auto_paging(self, **kwargs: Any) -> AsyncIterator[Subscription]:
        async for item in async_auto_paging_iter(self.list, **kwargs):
            yield item


class AsyncInvoices(_AsyncResource):
    """Async Invoices resource."""

    async def retrieve(self, invoice_id: str) -> Invoice:
        return Invoice.model_validate(await self._request("GET", f"/invoices/{invoice_id}"))

    async def list(self, **kwargs: Any) -> ListResponse[Invoice]:
        raw = await self._request("GET", "/invoices", params=kwargs)
        return ListResponse[Invoice].model_validate(raw)

    async def list_auto_paging(self, **kwargs: Any) -> AsyncIterator[Invoice]:
        async for item in async_auto_paging_iter(self.list, **kwargs):
            yield item


class AsyncStripeClient:
    """Asynchronous Stripe API client.

    Args:
        api_key: Your Stripe secret key (starts with ``sk_``).
        timeout: HTTP request timeout in seconds (default: 30).
        max_retries: Maximum number of retry attempts for retryable errors
            (default: 2).
        base_url: Override the Stripe API base URL.

    Example::

        async with stripewrap.AsyncStripeClient("sk_test_...") as client:
            customer = await client.customers.create(email="user@example.com")
            print(customer.id)
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
        self._http = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Stripe-Version": "2024-06-20",
                "User-Agent": "stripewrap/0.1.0 python-httpx",
            },
        )

        # Resource namespaces
        self.payment_intents = AsyncPaymentIntents(self)
        self.customers = AsyncCustomers(self)
        self.charges = AsyncCharges(self)
        self.refunds = AsyncRefunds(self)
        self.payment_methods = AsyncPaymentMethods(self)
        self.subscriptions = AsyncSubscriptions(self)
        self.invoices = AsyncInvoices(self)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"

        async def _do_request() -> dict[str, Any]:
            try:
                response = await self._http.request(
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
                _raise_for_response(response.status_code, json_body, request_id)

            return json_body

        return await retry_async(  # type: ignore[return-value]
            _do_request,
            max_retries=self._max_retries,
            retryable_status_codes=RETRYABLE_STATUS_CODES,
        )

    async def aclose(self) -> None:
        """Close the underlying async HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncStripeClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
