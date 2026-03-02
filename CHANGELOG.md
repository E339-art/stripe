# Changelog

All notable changes to `stripewrap` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `Event` and `EventData` Pydantic models for typed webhook event handling
- `PaymentIntent.amount_in_major_units` convenience property
- `SECURITY.md` with responsible disclosure policy
- `Makefile` with developer workflow shortcuts (`make check`, `make format`, etc.)
- `.pre-commit-config.yaml` for automated code quality checks
- Security scanning GitHub Actions workflow (weekly `pip-audit`)
- Python 3.13 support in CI matrix and classifiers
- Pip caching in CI for faster builds
- `ruff format --check` step in CI pipeline
- Logging support throughout retry and webhook modules
- `__repr__` methods on all Pydantic models for better debugging
- Coverage report configuration with 80% minimum threshold

### Fixed

- **Critical:** `hmac.new()` replaced with `hmac.HMAC()` in webhook signature
  verification (the previous call would raise `AttributeError` at runtime)
- Webhook signature header parsing now correctly handles multiple `v1` signatures
- `tolerance` parameter in `verify_header` / `construct_event` now properly
  typed as `int | None` to match documented behavior

### Changed

- Expanded ruff lint rules: added `RUF`, `PTH`, `C4`, `PIE` rule sets
- Added `isort` configuration for consistent import ordering
- Enhanced docstrings across all modules with Args/Returns/Raises sections
- Improved model docstrings explaining each Stripe resource
- Updated Codecov upload to use Python 3.13 matrix entry

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
- GitHub Actions CI: test matrix on Python 3.10 — 3.13 + ruff + mypy
- GitHub Actions publish workflow with PyPI Trusted Publishing (OIDC)
- Issue templates for bug reports and feature requests
- PR template with contribution checklist
- Examples: sync payment intent, async payment flow, webhook handler,
  customer list auto-pagination

[Unreleased]: https://github.com/E339-art/stripe/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/E339-art/stripe/releases/tag/v0.1.0
