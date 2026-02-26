# Changelog

All notable changes to `stripewrap` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-02-26

### Added

- `StripeClient` — synchronous Stripe client with httpx connection pooling
- `AsyncStripeClient` — fully async client with native `async/await`
- Pydantic v2 typed models: `Customer`, `PaymentIntent`, `Charge`, `Refund`,
  `Subscription`, `Invoice`, `PaymentMethod`, `ListResponse[T]`
- Typed exception hierarchy: `CardError`, `AuthenticationError`,
  `RateLimitError`, `InvalidRequestError`, `NotFoundError`, `APIError`,
  `APIConnectionError`, `IdempotencyError`, `SignatureVerificationError`
- `construct_event` / `verify_header` webhook signature verification
  (HMAC-SHA256, replay protection)
- `list_auto_paging` / `list_auto_paging` (async) for transparent
  auto-pagination across all list resources
- Retry with exponential backoff + full jitter on 429/5xx responses
- Resources: `payment_intents`, `customers`, `charges`, `refunds`,
  `payment_methods`, `subscriptions`, `invoices`
- GitHub Actions CI: test matrix on Python 3.10, 3.11, 3.12 + ruff + mypy
- GitHub Actions publish workflow with PyPI Trusted Publishing (OIDC)
- Issue templates for bug reports and feature requests
- PR template with contribution checklist
- Examples: sync payment intent, async payment flow, webhook handler,
  customer list auto-pagination

[Unreleased]: https://github.com/E339-art/stripe/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/E339-art/stripe/releases/tag/v0.1.0
