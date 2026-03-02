"""
Async example: create a customer and PaymentIntent using AsyncStripeClient.

Demonstrates:
  - async context manager usage
  - concurrent API calls with asyncio.gather
  - error handling in async code

Run with:
    STRIPE_API_KEY=sk_test_... python examples/async_payment_flow.py
"""

import asyncio
import os

import stripewrap


async def create_customer_and_intent(client: stripewrap.AsyncStripeClient) -> None:
    # Create customer and fetch existing customers concurrently
    customer, existing = await asyncio.gather(
        client.customers.create(
            email="ada@lovelace.dev",
            name="Ada Lovelace",
        ),
        client.customers.list(limit=5),
    )

    print(f"New customer:  {customer.id} ({customer.email})")
    print(f"Total fetched: {len(existing.data)} existing customers")

    # Create a PaymentIntent for the new customer
    intent = await client.payment_intents.create(
        amount=1999,  # $19.99
        currency="usd",
        customer=customer.id,
        description="Async payment example",
    )
    print(f"PaymentIntent: {intent.id} — {intent.status}")


async def main() -> None:
    api_key = os.environ.get("STRIPE_API_KEY", "sk_test_your_key_here")

    async with stripewrap.AsyncStripeClient(api_key=api_key) as client:
        try:
            await create_customer_and_intent(client)
        except stripewrap.AuthenticationError:
            print("ERROR: Invalid API key.")
        except stripewrap.StripeError as e:
            print(f"Stripe error [{e.http_status}]: {e.message}")


if __name__ == "__main__":
    asyncio.run(main())
