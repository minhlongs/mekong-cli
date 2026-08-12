#!/usr/bin/env python3
p = "src/services/vietqr_verifier.py"
with open(p) as f:
    src = f.read()

patches = [
    (
        'HEADER_NAME = "sepay-signature"',
        '    HEADER_NAME = "sepay-signature"',
    ),
    (
        '_ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")',
        '    _ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")',
    ),
    (
        "def __init__(self, secret: str) -> None:",
        "    def __init__(self, secret: str) -> None:",
    ),
]

for old, new in patches:
    if old not in src:
        print(f"MISSING: {old!r}")
    else:
        src = src.replace(old, new, 1)
        print(f"patched: {old!r}")

# Dedent the docstring / body lines that need to be inside the class
# Lines like " if not secret:" inside __init__ already match indent - check
with open(p, "w") as f:
    f.write(src)
print("written ok")
