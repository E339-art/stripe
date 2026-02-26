"""
Flask webhook handler with Stripe signature verification.

Demonstrates:
  - Using stripewrap.construct_event to verify signatures
  - Handling common event types with a match statement
  - Proper 400/200 response conventions Stripe expects

Requirements:
    pip install flask stripewrap

Run locally:
    STRIPE_WEBHOOK_SECRET=whsec_... flask --app examples/webhook_handler run --port 4242

Forward Stripe events to your local server (requires Stripe CLI):
    stripe listen --forward-to localhost:4242/webhook
"""

import os

from flask import Flask, Response, request

import stripewrap

app = Flask(__name__)

WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_your_secret_here")


@app.post("/webhook")
def stripe_webhook() -> Response:
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripewrap.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=WEBHOOK_SECRET,
        )
    except stripewrap.SignatureVerificationError as exc:
        print(f"Webhook verification failed: {exc}")
        return Response(str(exc), status=400)

    event_type = event["type"]
    data = event["data"]["object"]

    match event_type:
        case "payment_intent.succeeded":
            payment_intent_id = data["id"]
            amount = data["amount"] / 100
            currency = data["currency"].upper()
            print(f"PaymentIntent succeeded: {payment_intent_id} ({amount:.2f} {currency})")
            # TODO: fulfill the order

        case "payment_intent.payment_failed":
            error = data.get("last_payment_error", {})
            print(f"Payment failed: {error.get('message')}")
            # TODO: notify the customer

        case "customer.subscription.created":
            sub_id = data["id"]
            customer_id = data["customer"]
            print(f"Subscription created: {sub_id} for customer {customer_id}")
            # TODO: grant access

        case "customer.subscription.deleted":
            sub_id = data["id"]
            customer_id = data["customer"]
            print(f"Subscription cancelled: {sub_id} for customer {customer_id}")
            # TODO: revoke access

        case "invoice.payment_succeeded":
            invoice_id = data["id"]
            print(f"Invoice paid: {invoice_id}")

        case _:
            print(f"Unhandled event type: {event_type}")

    return Response(status=200)


if __name__ == "__main__":
    app.run(port=4242)
