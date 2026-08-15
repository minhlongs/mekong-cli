#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning (v12).

CLEAN SLATE — no accumulated cruft from v5-v11.
"""

import sys
import ast

TARGET = "src/api/billing_endpoints.py"

with open(TARGET, "r") as f:
    content = f.read()

# ── Phase 1: add trial_evaluator import (idempotent) ────────────────────────
ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"
if "from src.services.trial_evaluator import" not in content:
    content = content.replace(ANCHOR, ANCHOR + IMPORT, 1)
    print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# ── Phase 2: locate block ────────────────────────────────────────────────────
# BLOCK_START: function-level " if customer_id and price_id:\n"
# The block start is at offset 24586 in the ORIGINAL file, at 24663 after Phase 1 (+77)

BLOCK_START = " if customer_id and price_id:\n"
idx_start = content.find(BLOCK_START)
if idx_start == -1:
    sys.exit("ERROR: block start not found")
print(f"Step 2a: Block starts at offset {idx_start} (line {content[:idx_start].count(chr(10))+1})")

# The actual end marker in the file is: ")\n\n\n return {\n"
# Note: 1 space before "return", NOT 4 spaces
# After Phase 1 import addition, the block end shifts from 25963 → 26040
BLOCK_END = ")\n\n\n    return {\n"  # byte offset 25969-25993: ')' + 3×\n + 4 spaces
idx_end = content.find(BLOCK_END, idx_start + 500)
if idx_end == -1:
    # Diagnostic: show what we actually found at expected position
    expected = idx_start + 2000  # block is ~1400 chars, end should be ~idx_start+1450
    chunk = content[expected:expected + 50]
    print(f"\nERROR: BLOCK_END not found from idx_start+500={idx_start+500}")
    print("Content at expected+2000 position:")
    print(repr(chunk))
    sys.exit(1)

print(f"Step 2b: Block ends at offset {idx_end}")
print(f"Step 2c: Old block = {idx_end - idx_start} chars")

old_block = content[idx_start:idx_end]
print(f" Old head: {repr(old_block[:60])}")
print(f" Old tail: {repr(old_block[-60:])}")

# ── Sanity checks ────────────────────────────────────────────────────────────
checks_before = {
    "CreditStore present": "CreditStore().add_credits" in old_block,
    "not already patched": "is_trialing" not in old_block,
    "credits_provisioned present": "credits_provisioned = credits" in old_block,
}
for k, v in checks_before.items():
    print(f" [{('PASS' if v else 'FAIL')}] {k}")
if not all(checks_before.values()):
    sys.exit(f"Block validation failed: {checks_before}")

# ── Phase 3: build new block ─────────────────────────────────────────────────
# From live-file inspection of the original (pre-P1) file:
# The inner block (after "if customer_id and price_id:") at OFFSET 0 inside old_block:
# Line 1 (head): "    # Resolve tier...\n" → indent from old_block position → 8 spaces from function level
# We need to determine indentation from the OLD block, not assume.
# Strategy: find the LAST occurrence of BLOCK_END pattern in the OLD block
# and count leading spaces on that line.

# base_indent from old block: the `if customer_id` line is at S1=12 spaces,
# and all OTHER statement lines inside the block are at the SAME indent.
# credits_provisioned is deeper (S4=24) so we scan for a top-level statement instead.
# base_indent: indent of first non-blank, non-anchor statement line in old_block
for line in old_block.split("\n"):
    stripped = line.lstrip()
    if stripped and not stripped.startswith("if customer_id"):
        base_indent = len(line) - len(stripped)
        break
else:
    # Fallback: from BLOCK_START which has 1 space, statements at 12 = 1+11
    base_indent = len(old_block.split("\n")[0]) - len(old_block.split("\n")[0].lstrip()) + 11

print(f"Step 3a: Base indent from old block: {base_indent} spaces")

I1 = " " * base_indent          # top-level statements (inside if customer_id)
I2 = " " * (base_indent + 4)   # if/for/elif bodies
I3 = " " * (base_indent + 8)   # 2x nested
I4 = " " * (base_indent + 12)  # call close
I5 = " " * (base_indent + 16)  # deepest continuation

print(f"  I1={base_indent} I2={base_indent+4} I3={base_indent+8} I4={base_indent+12} I5={base_indent+16}")

# Build block
# NOTE: The section AFTER "if customer_id and price_id:" must be:
# 1. First blank line after "if" (consistent with original)
# 2. All statements at I1 (12 spaces)
# 3. The pattern: indent S1=12, S2=16, S3=20, S4=24, S5=28

new_block = (
    # Block start (matched by BLOCK_START anchor — identical)
    f"{I1}if customer_id and price_id:\n"
    "\n"

    # ── Trial detection ──────────────────────────────────────────────────────
    f'{I1}is_trialing = (subscription.get("status") or "").lower() == "trialing"\n'
    "\n"

    # ── Tier resolution ──────────────────────────────────────────────────────
    f"{I1}# Resolve tier from price_id via mapping\n"
    f"{I1}price_to_tier = get_tier_to_role_mapping()\n"
    f"{I1}tier_key = None\n"
    f"{I1}for pid, tk in price_to_tier.items():\n"
    f"{I2}if pid == price_id:\n"
    f"{I3}tier_key = tk\n"
    f"{I3}break\n"
    "\n"

    # ── Trial/tier credit resolution ─────────────────────────────────────────
    f"{I1}if is_trialing:\n"
    f'{I2}tier_key = "trial"\n'
    f'{I2}credits = tier_credits("trial")\n'
    f"{I1}elif tier_key:\n"
    f'{I2}credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    f"{I1}else:\n"
    f"{I2}credits = 0\n"
    "\n"

    # ── Resolve tenant_id via customer email ─────────────────────────────────
    f"{I1}# Find tenant_id from the customer's email\n"
    f"{I1}customer = await stripe_service._get_customer_by_id(customer_id)\n"
    f"{I1}if customer:\n"
    f"{I2}user_repo = UserRepository()\n"
    f"{I2}user = await user_repo.find_by_email(customer.email)\n"
    f"{I2}if user:\n"
    f"{I3}tenant_id = str(user.id)\n"
    "\n"

    # ── Persist trial dates in license metadata ──────────────────────────────
    f"{I2}# Store trial start/end dates in license when a trial subscription starts\n"
    f'{I2}if is_trialing and event_type in (\n'
    f'{I3}"customer.subscription.created",\n'
    f'{I3}"customer.subscription.updated",\n'
    f"{I2}):\n"
    f"{I3}trial_dates = compute_trial_dates()\n"
    f"{I3}license_repo = LicenseRepository()\n"
    f"{I3}license_info = await license_repo.get_license_by_key(\n"
    f'{I5}user.license_key if hasattr(user, "license_key") else tenant_id\n'
    f"{I3})\n"
    f"{I3}if license_info:\n"
    f'{I5}meta = license_info.get("metadata") or {{}}\n'
    f'{I5}if not meta.get("trial_started_at"):\n'
    f"{I5}meta.update(trial_dates)\n"
    f'{I5}meta["trial_status"] = "trial"\n'
    f"{I5}await license_repo.update_license(\n"
    f'{I5}license_info["key_id"], {{"metadata": meta}}\n'
    f"{I5})\n"
    f"{I5}logger.info(\n"
    f'{I5}"Persisted trial dates for key %s: %s",\n'
    f'{I5}license_info.get("key_id"), trial_dates,\n'
    f"{I5})\n"
    "\n"

    # ── Trial deletion: defer to evaluator for grace/expire ──────────────────
    f"{I2}# Defer trial subscription deletions to the evaluator (grace→expire)\n"
    f'{I2}if event_type == "customer.subscription.deleted" and is_trialing:\n'
    f"{I3}logger.info(\n"
    f'{I4}"Trial subscription deleted for %s — evaluator will handle grace window",\n'
    f"{I4}tenant_id,\n"
    f"{I3})\n"
    f"{I2}elif credits:\n"
    f"{I3}CreditStore().add_credits(\n"
    f"{I4}tenant_id=tenant_id,\n"
    f"{I4}amount=credits,\n"
    f'{I4}reason=f"stripe:{{event_type}}:{{event_id}}",\n'
    f"{I3})\n"
    f"{I3}credits_provisioned = credits\n"
    f"{I3}logger.info(\n"
    f'{I4}"Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    f"{I4}credits, tenant_id, tier_key, event_type,\n"
    f"{I3})\n"
)

print(f"Step 3: New block = {len(new_block)} chars (was {len(old_block)})")

# ── Phase 4: inject ──────────────────────────────────────────────────────────
new_content = content[:idx_start] + new_block + content[idx_end:]
print(f"Step 4: Total file = {len(new_content)} chars (was {len(content)})")

# ── Phase 5: write ────────────────────────────────────────────────────────────
with open(TARGET, "w") as f:
    f.write(new_content)
print("Step 5: Written to disk")

# ── Phase 6: syntax check ─────────────────────────────────────────────────────
try:
    ast.parse(new_content)
    print("Step 6: Syntax OK")
except SyntaxError as e:
    ctx = new_content.split("\n")[max(0, e.lineno - 5):e.lineno + 3]
    print(f"\nSYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.msg}")
    for i, line in enumerate(ctx):
        print(f" {max(1, e.lineno - 5 + i + 1)}: {repr(line)}")
    sys.exit(1)

# ── Phase 7: symbol checks ────────────────────────────────────────────────────
checks = {
    "is_trialing": "is_trialing" in new_content,
    "compute_trial_dates": "compute_trial_dates" in new_content,
    "evaluate_trial": "evaluate_trial" in new_content,
    "trial_status": "trial_status" in new_content,
    "LicenseRepository": "LicenseRepository" in new_content,
    "trial_started_at": "trial_started_at" in new_content,
    "deferring to evaluator": "deferring to evaluator" in new_content,
    "trial_evaluator import": "from src.services.trial_evaluator import" in new_content,
    'subscription.get("status")': 'subscription.get("status")' in new_content,
    "customer.subscription.deleted": "customer.subscription.deleted" in new_content,
    "CreditStore preserved": "CreditStore" in new_content,
    "tier_credits preserved": "tier_credits" in new_content,
    "return { preserved": "return {" in new_content,
    "credits_provisioned preserved": "credits_provisioned = credits" in new_content,
}
for k, v in checks.items():
    print(f" [{'PASS' if v else 'FAIL'}] {k}")

passing = sum(checks.values())
total = len(checks)
print(f"\nChecks: {passing}/{total} PASS")
if not all(checks.values()):
    failed = [k for k, v in checks.items() if not v]
    sys.exit(f"FAIL: {failed}")
print("All checks PASS — trial logic wired in")

# ── Phase 8: visual indentation check ─────────────────────────────────────────
lines = new_content.split('\n')
idx_s = new_content.find(' if customer_id and price_id:')
block_start_line = new_content[:idx_s].count('\n')
print(f"\nIndentation audit of patched block (line {block_start_line+1}):")
for i in range(block_start_line, block_start_line + 60):
    if i >= len(lines):
        break
    line = lines[i]
    if not line.strip():
        print(f" L{i+1:4d}: (blank)")
        continue
    spaces = len(line) - len(line.lstrip(' '))
    text = line.lstrip(' ')
    print(f" L{i+1:4d} ({spaces:2d}s): {repr(text[:70])}")
    if 'return {' in line:
        break
