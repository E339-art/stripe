"""Stripe webhook signature verification.

Stripe signs every webhook payload with a HMAC-SHA256 digest so you can
verify that events were sent by Stripe and not by a third party.

Usage::

    from stripewrap.webhooks import construct_event

    @app.post("/webhook")
    def handle_webhook(request):
        payload = request.body
        sig_header = request.headers["Stripe-Signature"]
        try:
            event = construct_event(payload, sig_header, webhook_secret)
        except SignatureVerificationError:
            return Response(status=400)
        ...
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any

from stripewrap.exceptions import SignatureVerificationError

logger = logging.getLogger(__name__)

DEFAULT_TOLERANCE = 300  # 5 minutes


def _compute_signature(payload: str, secret: str, timestamp: str) -> str:
    """Compute the expected HMAC-SHA256 signature.

    Args:
        payload: The raw request body as a string.
        secret: The signing secret (without ``whsec_`` prefix).
        timestamp: The Unix timestamp from the signature header.

    Returns:
        The hex-encoded HMAC-SHA256 digest.
    """
    signed_payload = f"{timestamp}.{payload}"
    return hmac.HMAC(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_header(
    payload: str | bytes,
    sig_header: str,
    secret: str,
    *,
    tolerance: int | None = DEFAULT_TOLERANCE,
) -> None:
    """Verify a Stripe webhook signature header.

    Args:
        payload: The raw request body exactly as received (bytes or str).
        sig_header: The value of the ``Stripe-Signature`` HTTP header.
        secret: Your webhook signing secret (starts with ``whsec_``).
        tolerance: Maximum age of the webhook in seconds before rejection.
            Set to ``None`` to disable timestamp validation.

    Raises:
        :class:`~stripewrap.exceptions.SignatureVerificationError`: If the
            signature is invalid or the timestamp is too old.
    """
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    try:
        elements = sig_header.split(",")
        parsed: dict[str, list[str]] = {}
        for element in elements:
            key, _, value = element.partition("=")
            parsed.setdefault(key.strip(), []).append(value.strip())
        timestamp = parsed["t"][0]
        signatures = parsed.get("v1", [])
    except (ValueError, KeyError, IndexError) as exc:
        raise SignatureVerificationError(
            "Unable to parse Stripe-Signature header",
            sig_header=sig_header,
        ) from exc

    if not signatures:
        raise SignatureVerificationError(
            "No v1 signatures found in Stripe-Signature header",
            sig_header=sig_header,
        )

    # Strip "whsec_" prefix if present
    signing_key = secret.removeprefix("whsec_")

    expected = _compute_signature(payload, signing_key, timestamp)

    if not any(hmac.compare_digest(expected, sig) for sig in signatures):
        logger.warning(
            "Webhook signature mismatch (request may have been tampered with)"
        )
        raise SignatureVerificationError(
            "Signature mismatch — the payload may have been tampered with",
            sig_header=sig_header,
        )

    if tolerance is not None:
        ts = int(timestamp)
        now = int(time.time())
        age = abs(now - ts)
        if age > tolerance:
            logger.warning(
                "Webhook timestamp too old: %ds > %ds tolerance", age, tolerance
            )
            raise SignatureVerificationError(
                f"Webhook timestamp is too old ({age}s > {tolerance}s tolerance). "
                "Ensure your server clock is synchronized.",
                sig_header=sig_header,
            )


def construct_event(
    payload: str | bytes,
    sig_header: str,
    secret: str,
    *,
    tolerance: int | None = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Verify the webhook signature and parse the event payload.

    This is the primary entry point for webhook handling. It combines
    signature verification with JSON parsing in a single call.

    Args:
        payload: The raw request body.
        sig_header: The ``Stripe-Signature`` header value.
        secret: Your webhook signing secret.
        tolerance: Maximum age in seconds. Set to ``None`` to disable.

    Returns:
        The parsed event as a dictionary. For typed access, construct a
        Pydantic model from the returned dict.

    Raises:
        :class:`~stripewrap.exceptions.SignatureVerificationError`: If
            verification fails.

    Example::

        event = construct_event(payload, sig_header, "whsec_...")
        if event["type"] == "payment_intent.succeeded":
            handle_success(event["data"]["object"])
    """
    verify_header(payload, sig_header, secret, tolerance=tolerance)

    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    return json.loads(payload)  # type: ignore[no-any-return]
