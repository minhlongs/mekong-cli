#!/usr/bin/env python3
"""Patch SepayVerifier to accept both sepay-signature and x-vietqr-signature."""

p = "src/services/vietqr_verifier.py"
with open(p) as f:
    src = f.read()

# 1. Add _ALIAS_HEADERS after HEADER_NAME
old1 = 'HEADER_NAME = "sepay-signature"'
new1 = 'HEADER_NAME = "sepay-signature"\n_ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")'
assert old1 in src
src = src.replace(old1, new1, 1)

# 2. Fix _extract_signature to check alias list
old2 = """def _extract_signature(self, headers: dict) -> str:
    # Headers dict may be case-mixed; normalize keys to lowercase
    for k, v in headers.items():
        if k.lower() == self.HEADER_NAME:
            return v.strip()
    return """"""

new2 = """def _extract_signature(self, headers: dict) -> str:
    # Headers dict may be case-mixed; normalize keys to lowercase
    for k, v in headers.items():
        kl = k.lower()
        if kl == self.HEADER_NAME or kl in self._ALIAS_HEADERS:
            return v.strip()
    return """"""

assert old2 in src, f"old2 not found — check indentation"
src = src.replace(old2, new2)

with open(p, "w") as f:
    f.write(src)
print("patched ok")
