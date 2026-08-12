#!/usr/bin/env python3
"""Fix two production bugs in billing_endpoints.py:
1. Insert tenant_id = customer_id fallback before customer lookup
2. De-dent the credit provisioning block by one level (S16->S12, S20->S16)
"""
import sys

TARGET = "src/api/billing_endpoints.py"

with open(TARGET) as f:
    lines = f.readlines()

# First, validate we're on a clean file
assert lines[773].strip() == "# Find tenant_id from the customer's email", \
    f"Unexpected L774 content: {repr(lines[773][:60])}"
print("Verified clean file state")

# ── Fix 1: Insert tenant_id = customer_id (S12) before customer lookup ───────
# L774 (0-indexed 773) = S12 "# Find tenant_id..."
lines.insert(773, "            tenant_id = customer_id\n")
print("Fix 1: tenant_id = customer_id added at L774 (S12)")

# ── Fix 2: De-dent lines 784-799 (0-indexed 783-798 after Fix1 insert) ───────
# These lines are at S16/S20 but belong at S12/S16 inside `if customer_id and price_id:` (S8)
# Only de-dent non-blank lines. Blank lines stay S0.
target_lines = range(783, 799)  # 0-indexed after Fix1 insert
for i in target_lines:
    line = lines[i]
    if line.strip() and len(line) > 0:
        lines[i] = line[4:]  # remove one indent level (4 spaces)
print("Fix 2: De-dented lines 784-799 by one level (S16→S12, S20→S16)")

new_content = "".join(lines)

# Syntax check
try:
    compile(new_content, TARGET, 'exec')
    print("Syntax: OK")
except SyntaxError as e:
    print(f"\nSYNTAX ERROR at L{e.lineno}: {e.msg}")
    ctx = new_content.split('\n')[max(0, e.lineno-5):e.lineno+3]
    for j, l in enumerate(ctx):
        spaces = len(l) - len(l.lstrip(' '))
        print(f"  L{e.lineno-5+j+1} S{spaces}: {repr(l[:70])}")
    sys.exit(1)

with open(TARGET, 'w') as f:
    f.write(new_content)
print("Written to disk\n")

# Verification
print("Verification (L754-L810):")
for i in range(753, 810):
    line = lines[i]
    spaces = len(line) - len(line.lstrip(' '))
    if line.strip():
        print(f"  L{i+1:4d} S{spaces:2d}: {repr(line[:70])}")
