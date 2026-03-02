"""stripewrap — The async-first Stripe SDK Python deserves.

Quick start::

    import stripewrap

    # Synchronous
    client = stripewrap.StripeClient("sk_test_...")
    intent = client.payment_intents.create(amount=2000, currency="usd")

    # Asynchronous
    async with stripewrap.AsyncStripeClient("sk_test_...") as client:
        intent = await client.payment_intents.create(amount=2000, currency="usd")
"""

from stripewrap.async_client import AsyncStripeClient
from stripewrap.client import StripeClient
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
)
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
from stripewrap.webhooks import construct_event, verify_header

__version__ = "0.1.0"
__all__ = [
    # Clients
    "StripeClient",
    "AsyncStripeClient",
    # Exceptions
    "StripeError",
    "AuthenticationError",
    "PermissionError",
    "InvalidRequestError",
    "NotFoundError",
    "CardError",
    "RateLimitError",
    "APIConnectionError",
    "APIError",
    "IdempotencyError",
    "SignatureVerificationError",
    # Models
    "ListResponse",
    "Customer",
    "PaymentIntent",
    "Charge",
    "Refund",
    "Subscription",
    "PaymentMethod",
    "Invoice",
    "Event",
    "EventData",
    "DeletedObject",
    # Webhooks
    "construct_event",
    "verify_header",
    # Version
    "__version__",
]
