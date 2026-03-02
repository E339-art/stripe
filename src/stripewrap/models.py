"""Pydantic v2 models for Stripe API resources.

All models use ``model_config = ConfigDict(extra="allow")`` so that
new fields added by Stripe won't cause validation errors. This ensures
forward compatibility as the Stripe API evolves.

Models are intentionally kept lightweight — they represent the most
commonly used fields for each resource. Any additional fields returned
by the API are still accessible via ``model.model_extra``.
"""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)


class StripeModel(BaseModel):
    """Base model for all Stripe API resources.

    Provides a shared configuration that allows extra fields (forward
    compatibility) and enables population by field name.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ---------------------------------------------------------------------------
# Generic list response
# ---------------------------------------------------------------------------


class ListResponse(StripeModel, Generic[T]):
    """A paginated list of Stripe objects.

    Attributes:
        data: The list of objects in this page.
        has_more: Whether there are more objects beyond this page.
        url: The URL for accessing this list endpoint.
        total_count: The total number of objects (only present on some endpoints).
    """

    object: Literal["list"] = "list"
    data: list[T]
    has_more: bool
    url: str
    total_count: int | None = None

    def __repr__(self) -> str:
        return f"ListResponse(count={len(self.data)}, has_more={self.has_more})"


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------


class Address(StripeModel):
    """A structured postal address."""

    city: str | None = None
    country: str | None = None
    line1: str | None = None
    line2: str | None = None
    postal_code: str | None = None
    state: str | None = None


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------


class Customer(StripeModel):
    """A Stripe Customer object.

    Customers allow you to perform recurring charges and track multiple
    charges that are associated with the same customer.
    """

    id: str
    object: Literal["customer"] = "customer"
    created: int
    email: str | None = None
    name: str | None = None
    phone: str | None = None
    description: str | None = None
    address: Address | None = None
    balance: int = 0
    currency: str | None = None
    delinquent: bool | None = None
    livemode: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
    tax_exempt: str | None = None

    def __repr__(self) -> str:
        return f"Customer(id={self.id!r}, email={self.email!r})"


# ---------------------------------------------------------------------------
# Card / Payment Method
# ---------------------------------------------------------------------------


class CardDetails(StripeModel):
    """Card-specific details on a PaymentMethod."""

    brand: str
    country: str | None = None
    exp_month: int
    exp_year: int
    fingerprint: str | None = None
    funding: str
    last4: str
    network: str | None = None

    def __repr__(self) -> str:
        return f"CardDetails(brand={self.brand!r}, last4={self.last4!r})"


class BillingDetails(StripeModel):
    """Billing information associated with a PaymentMethod."""

    address: Address | None = None
    email: str | None = None
    name: str | None = None
    phone: str | None = None


class PaymentMethod(StripeModel):
    """A Stripe PaymentMethod object.

    PaymentMethod objects represent a customer's payment instruments.
    You can use them with PaymentIntents to collect payments or save
    them to a Customer for future payments.
    """

    id: str
    object: Literal["payment_method"] = "payment_method"
    created: int
    customer: str | None = None
    livemode: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
    type: str
    billing_details: BillingDetails = Field(default_factory=BillingDetails)
    card: CardDetails | None = None

    def __repr__(self) -> str:
        return f"PaymentMethod(id={self.id!r}, type={self.type!r})"


# ---------------------------------------------------------------------------
# Payment Intent
# ---------------------------------------------------------------------------


class LastPaymentError(StripeModel):
    """Details about the last payment error on a PaymentIntent."""

    type: str
    code: str | None = None
    message: str | None = None
    param: str | None = None
    decline_code: str | None = None
    payment_method: PaymentMethod | None = None


class PaymentIntent(StripeModel):
    """A Stripe PaymentIntent object.

    A PaymentIntent guides you through the process of collecting a payment
    from your customer. It tracks charge attempts and records the payment
    state for you.
    """

    id: str
    object: Literal["payment_intent"] = "payment_intent"
    amount: int
    amount_capturable: int = 0
    amount_received: int = 0
    capture_method: str = "automatic"
    client_secret: str | None = None
    confirmation_method: str = "automatic"
    created: int
    currency: str
    customer: str | None = None
    description: str | None = None
    last_payment_error: LastPaymentError | None = None
    livemode: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
    next_action: dict[str, Any] | None = None
    payment_method: str | None = None
    payment_method_types: list[str] = Field(default_factory=list)
    receipt_email: str | None = None
    status: str
    statement_descriptor: str | None = None

    def __repr__(self) -> str:
        return (
            f"PaymentIntent(id={self.id!r}, amount={self.amount}, "
            f"currency={self.currency!r}, status={self.status!r})"
        )

    @property
    def amount_in_major_units(self) -> float:
        """Return the amount in major currency units (e.g. dollars)."""
        return self.amount / 100


# ---------------------------------------------------------------------------
# Charge
# ---------------------------------------------------------------------------


class Charge(StripeModel):
    """A Stripe Charge object.

    Charges represent a single attempt to move money into your Stripe
    account. PaymentIntents create Charges under the hood.
    """

    id: str
    object: Literal["charge"] = "charge"
    amount: int
    amount_captured: int = 0
    amount_refunded: int = 0
    captured: bool = False
    created: int
    currency: str
    customer: str | None = None
    description: str | None = None
    disputed: bool = False
    failure_code: str | None = None
    failure_message: str | None = None
    livemode: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
    paid: bool = False
    payment_intent: str | None = None
    payment_method: str | None = None
    receipt_email: str | None = None
    receipt_url: str | None = None
    refunded: bool = False
    status: str

    def __repr__(self) -> str:
        return (
            f"Charge(id={self.id!r}, amount={self.amount}, "
            f"currency={self.currency!r}, status={self.status!r})"
        )


# ---------------------------------------------------------------------------
# Refund
# ---------------------------------------------------------------------------


class Refund(StripeModel):
    """A Stripe Refund object.

    Refund objects allow you to refund a charge that has previously been
    created but not yet refunded.
    """

    id: str
    object: Literal["refund"] = "refund"
    amount: int
    charge: str | None = None
    created: int
    currency: str
    metadata: dict[str, str] = Field(default_factory=dict)
    payment_intent: str | None = None
    reason: str | None = None
    status: str

    def __repr__(self) -> str:
        return f"Refund(id={self.id!r}, amount={self.amount}, status={self.status!r})"


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------


class SubscriptionItem(StripeModel):
    """An item within a Subscription."""

    id: str
    object: Literal["subscription_item"] = "subscription_item"
    created: int
    metadata: dict[str, str] = Field(default_factory=dict)
    price: dict[str, Any]
    quantity: int | None = None
    subscription: str


class Subscription(StripeModel):
    """A Stripe Subscription object.

    Subscriptions allow you to charge a customer on a recurring basis.
    """

    id: str
    object: Literal["subscription"] = "subscription"
    cancel_at: int | None = None
    cancel_at_period_end: bool = False
    canceled_at: int | None = None
    collection_method: str = "charge_automatically"
    created: int
    currency: str
    current_period_end: int
    current_period_start: int
    customer: str
    default_payment_method: str | None = None
    description: str | None = None
    items: ListResponse[SubscriptionItem]
    livemode: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
    next_pending_invoice_item_invoice: int | None = None
    status: str
    trial_end: int | None = None
    trial_start: int | None = None

    def __repr__(self) -> str:
        return f"Subscription(id={self.id!r}, status={self.status!r})"


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------


class Invoice(StripeModel):
    """A Stripe Invoice object.

    Invoices are statements of amounts owed by a customer, generated
    automatically from subscriptions or created manually.
    """

    id: str
    object: Literal["invoice"] = "invoice"
    account_country: str | None = None
    amount_due: int
    amount_paid: int = 0
    amount_remaining: int
    created: int
    currency: str
    customer: str
    description: str | None = None
    livemode: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
    paid: bool = False
    status: str | None = None
    subscription: str | None = None
    total: int

    def __repr__(self) -> str:
        return (
            f"Invoice(id={self.id!r}, total={self.total}, "
            f"currency={self.currency!r}, status={self.status!r})"
        )


# ---------------------------------------------------------------------------
# Event (webhook payloads)
# ---------------------------------------------------------------------------


class EventData(StripeModel):
    """The data payload within a Stripe Event."""

    object: dict[str, Any]
    previous_attributes: dict[str, Any] | None = None


class Event(StripeModel):
    """A Stripe Event object.

    Events are created when an interesting change occurs in your Stripe
    account. They are delivered to your webhook endpoints.
    """

    id: str
    object: Literal["event"] = "event"
    api_version: str | None = None
    created: int
    data: EventData
    livemode: bool = False
    pending_webhooks: int = 0
    request: dict[str, Any] | None = None
    type: str

    def __repr__(self) -> str:
        return f"Event(id={self.id!r}, type={self.type!r})"


# ---------------------------------------------------------------------------
# Deleted object stub
# ---------------------------------------------------------------------------


class DeletedObject(StripeModel):
    """Represents a deleted Stripe object.

    Returned by delete operations to confirm the object was removed.
    """

    id: str
    object: str
    deleted: Literal[True] = True

    def __repr__(self) -> str:
        return f"DeletedObject(id={self.id!r}, object={self.object!r})"
