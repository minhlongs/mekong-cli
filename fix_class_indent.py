#!/usr/bin/env python3
"""Fix SepayVerifier: add 4-space indent to class-level definitions."""
p = "src/services/vietqr_verifier.py"
with open(p) as f:
    lines = f.readlines()

# Target lines: class-level definitions inside SepayVerifier that are at column 0
fixes = {
    34: 'HEADER_NAME = "sepay-signature"',
    35: '_ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")',
    37: "def __init__(self, secret: str) -> None:",
    42: "def verify(self, body: bytes, headers: dict) -> bool:",
    50: "def _extract_signature(self, headers: dict) -> str:",
}

for lineno, text in fixes.items():
    idx = lineno - 1
    actual = lines[idx].rstrip("\n")
    if actual == text:
        lines[idx] = "    " + actual + "\n"
        print(f"L{lineno}: fixed")
    else:
        print(f"L{lineno}: SKIP (actual={actual!r})")

with open(p, "w") as f:
    f.writelines(lines)
print("written")
