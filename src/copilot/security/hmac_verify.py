"""Jira webhook signature verification (HMAC-SHA256 over the raw body)."""

from __future__ import annotations

import hashlib
import hmac


def compute_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, body: bytes, signature: str | None) -> bool:
    """Constant-time comparison, never use `==` on secrets."""
    if not signature:
        return False
    return hmac.compare_digest(compute_signature(secret, body), signature)
