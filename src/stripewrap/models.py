"""Pydantic v2 models for Stripe API resources.

All models use ``model_config = ConfigDict(extra="allow")`` so that
new fields added by Stripe won't cause validation errors.
"""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)


class StripeModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ---------------------------------------------------------------------------
# Generic list response
# ---------------------------------------------------------------------------


class ListResponse(StripeModel, Generic[T]):
    """A paginated list of Stripe objects."""

    object: Literal["list"] = "list"
    data: list[T]
    has_more: bool
    url: str
    total_count: int | None = None


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------


class Address(StripeModel):
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


# ---------------------------------------------------------------------------
# Card / Payment Method
# ---------------------------------------------------------------------------


class CardDetails(StripeModel):
    brand: str
    country: str | None = None
    exp_month: int
    exp_year: int
    fingerprint: str | None = None
    funding: str
    last4: str
    network: str | None = None


class BillingDetails(StripeModel):
    address: Address | None = None
    email: str | None = None
    name: str | None = None
    phone: str | None = None


class PaymentMethod(StripeModel):
    id: str
    object: Literal["payment_method"] = "payment_method"
    created: int
    customer: str | None = None
    livemode: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
    type: str
    billing_details: BillingDetails = Field(default_factory=BillingDetails)
    card: CardDetails | None = None


# ---------------------------------------------------------------------------
# Payment Intent
# ---------------------------------------------------------------------------


class LastPaymentError(StripeModel):
    type: str
    code: str | None = None
    message: str | None = None
    param: str | None = None
    decline_code: str | None = None
    payment_method: PaymentMethod | None = None


class PaymentIntent(StripeModel):
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


# ---------------------------------------------------------------------------
# Charge
# ---------------------------------------------------------------------------


class Charge(StripeModel):
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


# ---------------------------------------------------------------------------
# Refund
# ---------------------------------------------------------------------------


class Refund(StripeModel):
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


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------


class SubscriptionItem(StripeModel):
    id: str
    object: Literal["subscription_item"] = "subscription_item"
    created: int
    metadata: dict[str, str] = Field(default_factory=dict)
    price: dict[str, Any]
    quantity: int | None = None
    subscription: str


class Subscription(StripeModel):
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


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------


class Invoice(StripeModel):
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


# ---------------------------------------------------------------------------
# Deleted object stub
# ---------------------------------------------------------------------------


class DeletedObject(StripeModel):
    id: str
    object: str
    deleted: Literal[True] = True
