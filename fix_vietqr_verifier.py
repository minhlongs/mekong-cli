#!/usr/bin/env python3
"""Fix SepayVerifier to accept both sepay-signature and x-vietqr-signature headers."""

p = "src/services/vietqr_verifier.py"
with open(p) as f:
    src = f.read()

old = '_ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")\n'
new = ''

# 1) Remove the duplicate alias block if present
src = src.replace(
    '_ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")\n',
    '')
src = src.replace(
    '# Alias accepted for test compatibility and provider convergence.\n_ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")\n',
    '')

# 2) Fix _extract_signature to check the alias list
old_extract = (
    "    for k, v in headers.items():\n"
    "        if k.lower() == self.HEADER_NAME:\n"
    "            return v.strip()\n"
    "    return \"\""
)
new_extract = (
    "    for k, v in headers.items():\n"
    "        kl = k.lower()\n"
    "        if kl == self.HEADER_NAME or kl in self._ALIAS_HEADERS:\n"
    "            return v.strip()\n"
    "    return \"\""
)
assert old_extract in src, f"old_extract block not found"
src = src.replace(old_extract, new_extract)

with open(p, "w") as f:
    f.write(src)
print("ok")
