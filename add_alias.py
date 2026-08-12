#!/usr/bin/env python3
p = "src/services/vietqr_verifier.py"
with open(p) as f:
    src = f.read()

src = src.replace(
    'HEADER_NAME = "sepay-signature"',
    'HEADER_NAME = "sepay-signature"\n_ALIAS_HEADERS = ("sepay-signature", "x-vietqr-signature")'
)

with open(p, "w") as f:
    f.write(src)

with open(p) as f:
    verify = f.read()
assert "_ALIAS_HEADERS = " in verify, "insertion failed"
print("ok")
