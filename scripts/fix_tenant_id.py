#!/usr/bin/env python3
"""Fix two bugs in billing_endpoints.py tenant_id handling."""

TARGET = "src/api/billing_endpoints.py"

with open(TARGET) as f:
    lines = f.readlines()

# ── Fix 1: tenant_id fallback ─────────────────────────────────────────────────
# Insert "tenant_id = customer_id" (S8) before line 775 (customer lookup)
lines.insert(774, "        tenant_id = customer_id\n")  # S8

# ── Fix 2: credits_provisioned scope ─────────────────────────────────────────
# After insert, old line 795 becomes line 796. Find and remove old block.
old_cp_line = None
for i, line in enumerate(lines):
    if line.strip() == "credits_provisioned = credits":
        old_cp_line = i
        break
assert old_cp_line is not None, "credits_provisioned line not found"

# Remove 5 lines: credits_provisioned + logger.info(...) block
del lines[old_cp_line:old_cp_line + 5]

# Find CreditStore close " )" near the deleted range
cs_close_idx = None
for i in range(old_cp_line - 5, old_cp_line + 10):
    if i >= 0 and i < len(lines) and lines[i].strip() == ")":
        if i > 0 and "reason=" in lines[i - 1]:
            cs_close_idx = i
            break
assert cs_close_idx is not None, "CreditStore close not found"

# Insert properly-indented block AFTER CreditStore close (inside elif credits)
# S12 = 12 spaces for elif body
new_block = [
    "            credits_provisioned = credits\n",
    "            logger.info(\n",
    '                "Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n',
    "                credits, tenant_id, tier_key, event_type,\n",
    "            )\n",
]
for j, new_line in enumerate(new_block):
    lines.insert(cs_close_idx + 1 + j, new_line)

with open(TARGET, "w") as f:
    f.writelines(lines)

print("Fix 1: tenant_id = customer_id fallback added (S8)")
print("Fix 2: credits_provisioned + logger moved inside elif credits block (S12)")

# Verify
import ast  # noqa: E402
ast.parse("".join(lines))
print("Syntax: OK")

# Show result
content = "".join(lines)
idx = content.find("# Find tenant_id")
for line in content[idx:idx + 350].split("\n")[:35]:
    spaces = len(line) - len(line.lstrip(" "))
    print(f" S{spaces:2d}: {repr(line[:75])}")
