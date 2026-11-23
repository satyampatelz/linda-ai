"""HMAC-SHA256 verification of Meta webhook signatures.

Meta signs every webhook POST body with the app secret and sends it as
`X-Hub-Signature-256: sha256=<hex>`. Verification uses a constant-time
compare so a forged signature can't be probed byte by byte.
"""
import hashlib
import hmac


def verify_signature(raw_body: bytes, signature_header, app_secret: str) -> bool:
    """True if the header matches HMAC-SHA256(body, app_secret).

    Returns False when the secret is empty, the header is missing or
    malformed, or the digest doesn't match. The webhook handler decides
    what "no secret configured" means (it skips verification and logs a
    warning — the user should set the secret in Settings).
    """
    if not app_secret:
        return False
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)
