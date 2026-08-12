#!/usr/bin/env python3
"""Fix indentation of lines 782-803 in billing_endpoints.py.

The trial logic block (evaluate_trial call + credits_provisioned)
has extra 4-space indent — shifts all lines 782-803 left by 4 spaces.
Also inserts tenant_id = customer_id fallback before customer lookup.
"""
import sys

TARGET = "src/api/billing_endpoints.py"

with open(TARGET) as f:
    lines = f.readlines()

# ── Fix 1: Insert tenant_id = customer_id before customer lookup ──────────────
# Line 774 (0-indexed 773) = "            # Find tenant_id..."  (S12)
lines.insert(773, "            tenant_id = customer_id\n")
print("Fix 1: Inserted tenant_id = customer_id at L774 (S12=12 spaces)")

# ── Fix 2: Shift lines 782-803 left by 4 spaces ──────────────────────────────
# After Fix1 insert, old line 782 is now at 0-indexed 783 (which is S16 in file)
# These lines belong inside `if customer_id and price_id:` (S8 body = S12)
# Lines 784-804 need S16→S12, S20→S16 shifts
for i in range(783, 803 + 1):  # 0-indexed: lines 784-804 in the file
    line = lines[i]
    if line.strip() and line.startswith("    "):
        lines[i] = line[4:]  # strip one 4-space indent level
    # blank lines: untouched (they pass line.strip() == "" check)

print("Fix 2: Shifted lines 784-803 left by 4 spaces (S16→S12, S20→S16)")

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
print("Written to disk")

# Verify: show lines 770-810
print("\nVerification (L770-L810):")
for i in range(769, min(810, len(lines))):
    line = lines[i]
    spaces = len(line) - len(line.lstrip(' '))
    if line.strip():
        print(f"  L{i+1:4d} S{spaces:2d}: {repr(line[:75])}")
