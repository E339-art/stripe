# stripewrap

[![CI](https://github.com/E339-art/stripe/actions/workflows/ci.yml/badge.svg)](https://github.com/E339-art/stripe/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/stripewrap.svg)](https://pypi.org/project/stripewrap/)
[![Python versions](https://img.shields.io/pypi/pyversions/stripewrap.svg)](https://pypi.org/project/stripewrap/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Coverage](https://codecov.io/gh/E339-art/stripe/branch/main/graph/badge.svg)](https://codecov.io/gh/E339-art/stripe)
[![Downloads](https://static.pepy.tech/badge/stripewrap/month)](https://pepy.tech/project/stripewrap)

**Modern, async-first Python SDK for Stripe.** Fully typed with Pydantic v2, batteries-included retry and pagination, and a test-friendly architecture — so you can stop fighting your payment library and start shipping.

```bash
pip install stripewrap
```

---

## Why not the official `stripe-python`?

| Feature | `stripe-python` | `stripewrap` |
|---|:---:|:---:|
| Native async/await | Partial | ✅ Full |
| Pydantic v2 type-safe models | ✗ | ✅ |
| Typed exception hierarchy | ✗ | ✅ |
| Auto-pagination | Manual | ✅ `for item in client.customers.list_auto_paging()` |
| Retry with jitter | ✗ | ✅ |
| Easy testing (no monkey-patching) | ✗ | ✅ |
| IDE autocompletion on responses | Partial | ✅ Full |

---

## Quick Start

```python
import stripewrap

client = stripewrap.StripeClient(api_key="sk_test_...")

# Create a customer — returns a typed Customer object
customer = client.customers.create(
    email="grace@example.com",
    name="Grace Hopper",
    metadata={"plan": "enterprise"},
)
print(customer.id)      # cus_xyz
print(customer.name)    # 'Grace Hopper'

# Create a PaymentIntent — amount in cents
intent = client.payment_intents.create(
    amount=4999,        # $49.99
    currency="usd",
    customer=customer.id,
    description="Supercompiler Pro subscription",
)
print(intent.status)   # 'requires_payment_method'
```

---

## Async Usage

```python
import asyncio
import stripewrap

async def main():
    async with stripewrap.AsyncStripeClient(api_key="sk_test_...") as client:
        # Create a customer asynchronously
        customer = await client.customers.create(email="ada@example.com")
        print(customer.id)

        # Auto-paginate all charges without any cursor bookkeeping
        async for charge in client.charges.list_auto_paging(limit=100):
            print(f"{charge.id}: {charge.currency.upper()} {charge.amount / 100:.2f}")

asyncio.run(main())
```

---

## Typed Error Handling

Every error surfaces exactly the context you need — no dict drilling:

```python
import stripewrap

client = stripewrap.StripeClient(api_key="sk_test_...")

try:
    intent = client.payment_intents.create(amount=2000, currency="usd")
except stripewrap.CardError as e:
    print(f"Card declined:  {e.decline_code}")  # e.g. 'insufficient_funds'
    print(f"Stripe code:    {e.code}")
    print(f"Request ID:     {e.request_id}")    # for Stripe support tickets
except stripewrap.RateLimitError:
    # Automatic retries handle transient 429s; this catches the final failure
    print("Rate limited after retries exhausted")
except stripewrap.AuthenticationError:
    print("Invalid API key — check STRIPE_SECRET_KEY")
except stripewrap.StripeError as e:
    # Catch-all — full context still available
    print(f"Stripe error [{e.http_status}]: {e.message}")
```

**Exception hierarchy:**

```
StripeError
├── AuthenticationError    (401 — bad API key)
├── PermissionError        (403 — insufficient permissions)
├── InvalidRequestError    (400 — bad parameters; .param tells you which one)
├── NotFoundError          (404)
├── CardError              (402 — .decline_code, .charge)
├── RateLimitError         (429 — retried automatically)
├── APIConnectionError     (network failure — retried automatically)
├── APIError               (5xx server errors)
├── IdempotencyError       (400 idempotency key reuse)
└── SignatureVerificationError (webhook signature mismatch)
```

---

## Auto-Pagination

Stripe paginates all list endpoints. `stripewrap` handles this transparently:

```python
# Sync — iterate every customer across all pages
for customer in client.customers.list_auto_paging(limit=100):
    send_newsletter(customer.email)

# Async version
async for customer in async_client.customers.list_auto_paging(limit=100):
    await send_newsletter(customer.email)
```

Under the hood, the cursor (`starting_after`) advances automatically on every page.
No `while has_more` loops. No manual `starting_after` bookkeeping.

---

## Webhook Handling

```python
# FastAPI example
from fastapi import FastAPI, Header, HTTPException, Request
import stripewrap

app = FastAPI()

@app.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
):
    body = await request.body()
    try:
        event = stripewrap.construct_event(
            payload=body,
            sig_header=stripe_signature,
            secret="whsec_...",
        )
    except stripewrap.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    match event["type"]:
        case "payment_intent.succeeded":
            await fulfill_order(event["data"]["object"]["id"])
        case "customer.subscription.deleted":
            await cancel_access(event["data"]["object"]["customer"])

    return {"received": True}
```

`construct_event` verifies the HMAC-SHA256 signature **and** rejects replayed
events older than 5 minutes — protecting against replay attacks out of the box.

---

## Testing Your Integration

Because `StripeClient` uses `httpx` under the hood, testing is trivial — no
monkey-patching required:

```python
import pytest
import respx
from httpx import Response
import stripewrap

def test_create_customer():
    with respx.mock:
        respx.post("https://api.stripe.com/v1/customers").mock(
            return_value=Response(200, json={
                "id": "cus_mock", "object": "customer",
                "livemode": False, "created": 1700000000,
            })
        )
        client = stripewrap.StripeClient(api_key="sk_test_fake", max_retries=0)
        customer = client.customers.create(email="test@example.com")

    assert customer.id == "cus_mock"
```

---

## Installation

```bash
# Latest stable release
pip install stripewrap

# With version pin (recommended for production)
pip install "stripewrap>=0.1,<1.0"
```

**Requirements:** Python 3.10+, `httpx>=0.27`, `pydantic>=2.0`

---

## Configuration

```python
import stripewrap

client = stripewrap.StripeClient(
    api_key="sk_test_...",
    timeout=60.0,          # request timeout in seconds (default: 30)
    max_retries=3,         # retries on 429/5xx (default: 2)
    base_url="http://localhost:12111/v1",  # override for local testing
)
```

Use as a context manager to ensure the HTTP connection pool is properly closed:

```python
with stripewrap.StripeClient(api_key="sk_test_...") as client:
    customers = list(client.customers.list_auto_paging())

# Async version
async with stripewrap.AsyncStripeClient(api_key="sk_test_...") as client:
    intent = await client.payment_intents.create(amount=1000, currency="eur")
```

---

## API Coverage

| Resource | Sync | Async | Auto-paginate |
|---|:---:|:---:|:---:|
| Customers | ✅ | ✅ | ✅ |
| PaymentIntents | ✅ | ✅ | ✅ |
| Charges | ✅ | ✅ | ✅ |
| Refunds | ✅ | ✅ | ✅ |
| PaymentMethods | ✅ | ✅ | — |
| Subscriptions | ✅ | ✅ | ✅ |
| Invoices | ✅ | ✅ | ✅ |
| Webhooks | ✅ | ✅ | — |

More resources coming — PRs welcome!

---

## Examples

See the [`examples/`](examples/) directory for runnable scripts:

- [`create_payment_intent.py`](examples/create_payment_intent.py) — Sync payment flow
- [`async_payment_flow.py`](examples/async_payment_flow.py) — Async payment flow
- [`webhook_handler.py`](examples/webhook_handler.py) — Flask webhook receiver
- [`list_customers.py`](examples/list_customers.py) — Auto-pagination walkthrough

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup
instructions, coding standards, and the PR process.

```bash
git clone https://github.com/E339-art/stripe
cd stripe
pip install -e ".[dev]"
pytest tests/ -v         # all tests should pass
ruff check .             # linting
```

---

## License

[MIT](LICENSE) — Copyright 2026 E339-art
