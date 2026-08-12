#!/usr/bin/env python3
"""Rewrite SepayVerifier class body with consistent indentation."""
p = "src/services/vietqr_verifier.py"
with open(p) as f:
    src = f.read()

# Replace the broken SepayVerifier body
old = '''class SepayVerifier:
    """HMAC-SHA256 over raw body, signature in `Sepay-Signature` header.

    Sepay docs: https://sepay.vn/docs/webhook (signature scheme).
    Header name is case-insensitive per HTTP spec; we look up via
    lowercase to be robust to ASGI middleware lowercasing.
    """

 HEADER_NAME = "sepay-signature"
 _ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")

 def __init__(self, secret: str) -> None:
    if not secret:
        raise ValueError("SepayVerifier requires non-empty secret")
    self._secret = secret.encode("utf-8")

 def verify(self, body: bytes, headers: dict) -> bool:
    received = self._extract_signature(headers)
    if not received:
        return False
    expected = hmac.new(self._secret, body, hashlib.sha256).hexdigest()
    # Timing-safe comparison — equal-length both sides
    return hmac.compare_digest(expected, received)

 def _extract_signature(self, headers: dict) -> str:
    # Headers dict may be case-mixed; normalize keys to lowercase
    for k, v in headers.items():
        kl = k.lower()
        if kl == self.HEADER_NAME or kl in self._ALIAS_HEADERS:
            return v.strip()
    return ""'''

new = '''class SepayVerifier:
    """HMAC-SHA256 over raw body, signature in `Sepay-Signature` header.

    Sepay docs: https://sepay.vn/docs/webhook (signature scheme).
    Header name is case-insensitive per HTTP spec; we look up via
    lowercase to be robust to ASGI middleware lowercasing.
    """

    HEADER_NAME = "sepay-signature"
    _ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")

    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError("SepayVerifier requires non-empty secret")
        self._secret = secret.encode("utf-8")

    def verify(self, body: bytes, headers: dict) -> bool:
        received = self._extract_signature(headers)
        if not received:
            return False
        expected = hmac.new(self._secret, body, hashlib.sha256).hexdigest()
        # Timing-safe comparison — equal-length both sides
        return hmac.compare_digest(expected, received)

    def _extract_signature(self, headers: dict) -> str:
        # Headers dict may be case-mixed; normalize keys to lowercase
        for k, v in headers.items():
            kl = k.lower()
            if kl == self.HEADER_NAME or kl in self._ALIAS_HEADERS:
                return v.strip()
        return ""'''

if old not in src:
    print("old block not found")
    # Show what's actually there
    import re
    m = re.search(r'class SepayVerifier:.*?(?=\nclass )', src, re.DOTALL)
    if m:
        print("actual SepayVerifier:")
        print(repr(m.group()[:300]))
else:
    src = src.replace(old, new)
    with open(p, "w") as f:
        f.write(src)
    import ast
    ast.parse(src)
    print("ok")
