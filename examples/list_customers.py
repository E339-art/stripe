"""
Auto-pagination example: iterate all customers without managing cursors.

stripewrap handles the has_more / starting_after pagination loop automatically.
This script counts all customers in your account.

Run with:
    STRIPE_API_KEY=sk_test_... python examples/list_customers.py
"""

import os

import stripewrap

api_key = os.environ.get("STRIPE_API_KEY", "sk_test_your_key_here")
client = stripewrap.StripeClient(api_key=api_key)

print("Fetching all customers (auto-paging)...")
count = 0

try:
    for customer in client.customers.list_auto_paging(limit=100):
        count += 1
        if count <= 5:
            print(f"  {customer.id}: {customer.email or '(no email)'}")
        elif count == 6:
            print("  ...")

    print(f"\nTotal customers: {count}")

except stripewrap.AuthenticationError:
    print("ERROR: Invalid API key. Set STRIPE_API_KEY to a valid sk_test_... key.")
except stripewrap.StripeError as e:
    print(f"Stripe error: {e.message}")
finally:
    client.close()
