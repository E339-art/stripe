"""
Sync example: create a PaymentIntent and handle common errors.

Run with:
    STRIPE_API_KEY=sk_test_... python examples/create_payment_intent.py
"""

import os

import stripewrap

api_key = os.environ.get("STRIPE_API_KEY", "sk_test_your_key_here")
client = stripewrap.StripeClient(api_key=api_key)

try:
    # Create a customer first
    customer = client.customers.create(
        email="grace@example.com",
        name="Grace Hopper",
        metadata={"source": "stripewrap_example"},
    )
    print(f"Customer created: {customer.id} ({customer.email})")

    # Create a PaymentIntent for $49.99
    intent = client.payment_intents.create(
        amount=4999,  # always in the smallest currency unit (cents for USD)
        currency="usd",
        customer=customer.id,
        description="Supercompiler Pro — Annual subscription",
        metadata={"plan": "pro_annual"},
    )
    print(f"PaymentIntent:   {intent.id}")
    print(f"Amount:          ${intent.amount / 100:.2f} {intent.currency.upper()}")
    print(f"Status:          {intent.status}")
    print(f"Client secret:   {intent.client_secret[:20]}...")

    # In a real app you'd send client_secret to the frontend to complete payment
    # with Stripe.js / Stripe Elements

except stripewrap.AuthenticationError:
    print("ERROR: Invalid API key. Set STRIPE_API_KEY to a valid sk_test_... key.")
except stripewrap.CardError as e:
    print(f"Card declined: {e.decline_code} — {e.message}")
except stripewrap.StripeError as e:
    print(f"Stripe error [{e.http_status}]: {e.message}")
finally:
    client.close()
