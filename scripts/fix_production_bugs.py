#!/usr/bin/env python3
"""Fix two production bugs in billing_endpoints.py."""
import sys

TARGET = "src/api/billing_endpoints.py"

with open(TARGET) as f:
    content = f.read()

lines = content.split('\n')

# ── Fix 1: Add tenant_id fallback ─────────────────────────────────────────────
# Line 774 (0-indexed 773) = "    # Find tenant_id from the customer's email"
# Insert "    tenant_id = customer_id" BEFORE line 774 (same S12 indent)
idx = 773  # 0-indexed line 774
assert "# Find tenant_id" in lines[idx], f"Fix 1 target not at line {idx+1}: {repr(lines[idx])}"
lines.insert(idx, "    tenant_id = customer_id")
print(f"Fix 1: Inserted tenant_id = customer_id at L{idx+1} (S12)")

# ── Fix 2: Fix indentation of lines 782-799 ──────────────────────────────────
# After insert, old lines shift by +1.
# Old line 782 → new line 783 (S16): "# Signal evaluator..." → should be S12
# Old line 783 → new line 784 (S16): "if is_trialing:" → should be S12
# Lines 784-788: evaluate_trial call → S16→S20 (relative to new S12 parent, OK as S16)
# Old line 789 → new line 790 (S16): "elif credits:" → should be S12
# Old line 790-799: CreditStore + logger block → should be S12-S16, currently S16-S20

# Lines affected (0-indexed after insert):
# 0: S16 "# Signal evaluator..." → S12 (remove 4 spaces)
# 1: S16 "if is_trialing:" → S12 (remove 4 spaces)
# 2: S20 "evaluate_trial(" → S16 (remove 4 spaces)  [args → S20, OK relative]
# 3: S24 "    tenant_id=tenant_id," → S20 (remove 4 spaces)
# 4: S24 "    customer_id=customer_id," → S20 (remove 4 spaces)
# 5: S24 "    event_type=event_type," → S20 (remove 4 spaces)
# 6: S20 ")" → S16 (remove 4 spaces)
# 7: S16 "elif credits:" → S12 (remove 4 spaces)
# 8: S20 "CreditStore().add_credits(" → S16 (remove 4 spaces)
# 9: S24 "    tenant_id=tenant_id," → S20 (remove 4 spaces)
# 10: S24 "    amount=credits," → S20 (remove 4 spaces)
# 11: S24 "    reason=..." → S20 (remove 4 spaces)
# 12: S20 ")" → S16 (remove 4 spaces)
# 13: S20 "credits_provisioned = credits" → S16 (remove 4 spaces)
# 14: S20 "logger.info(" → S16 (remove 4 spaces)
# 15: S24 "    ...format string..." → S20 (remove 4 spaces)
# 16: S24 "    credits, tenant_id..." → S20 (remove 4 spaces)
# 17: S20 ")" → S16 (remove 4 spaces)

fix2_lines = range(783, 801)  # 0-indexed lines to adjust (after Fix1 insert)
for i in fix2_lines:
    line = lines[i]
    if not line.strip():
        continue
    spaces = len(line) - len(line.lstrip(' '))
    if spaces >= 4:
        lines[i] = line[4:]  # remove 4 leading spaces

print("Fix 2: Fixed indentation of lines 784-800 (S16→S12, S20→S16)")

new_content = '\n'.join(lines)

# Syntax check
try:
    compile(new_content, TARGET, 'exec')
    print("Syntax: OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR at L{e.lineno}: {e.msg}")
    ctx = new_content.split('\n')[max(0,e.lineno-5):e.lineno+2]
    for j, l in enumerate(ctx):
        spaces = len(l) - len(l.lstrip(' '))
        print(f"  L{e.lineno-5+j} S{spaces}: {repr(l[:70])}")
    sys.exit(1)

with open(TARGET, 'w') as f:
    f.write(new_content)
print("Written to disk")
print("\nVerification:")
for i in range(770, 802):
    line = lines[i]
    spaces = len(line) - len(line.lstrip(' '))
    if line.strip():
        print(f"  L{i+1:4d} S{spaces:2d}: {repr(line[:75])}")
