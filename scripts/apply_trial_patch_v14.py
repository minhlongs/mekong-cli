#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning (v14).

Verified indentation from live file:
  S8  = 8 spaces  — 'if customer_id and price_id:' anchor
  S12 = 12 spaces — top-level statements inside the if block
  S16 = 16 spaces — body of inner if/for (1 level deeper)
  S20 = 20 spaces — 2 levels deeper
  S24 = 24 spaces — CreditStore close, logger close, tenant_id = ...
  S28 = 28 spaces — fn call continuations (kwargs, logger args)
  S4  = 4 spaces  — 'return {' at function level
"""

import sys
import ast

TARGET = "src/api/billing_endpoints.py"

with open(TARGET, "r") as f:
    content = f.read()

# ── Phase 1: add trial_evaluator import (idempotent) ──────────────────────────
ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"
if "from src.services.trial_evaluator import" not in content:
    content = content.replace(ANCHOR, ANCHOR + IMPORT, 1)
    print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# ── Phase 2: locate block ─────────────────────────────────────────────────────
# The `if customer_id and price_id:` line has 8 leading spaces in the file.
# But the block itself is a logical unit — we match by content, not indent.
# We search for 'if customer_id and price_id:' then find the closing ')'
# followed by 3 newlines and 4 spaces + 'return{'

BLOCK_START_MARKER = "if customer_id and price_id:"
BLOCK_END_MARKER = ")\n\n\n    return {\n"  # 4 spaces before return at function level (S4)

idx_start = content.find(BLOCK_START_MARKER)
if idx_start == -1:
    sys.exit("ERROR: block start not found")
print(f"Step 2a: Block starts at offset {idx_start} (line {content[:idx_start].count(chr(10))+1})")

# Find the matching BLOCK_END after the block start
idx_end = content.find(BLOCK_END_MARKER, idx_start + 500)
if idx_end == -1:
    sys.exit("ERROR: block end not found — is the file already patched?")
print(f"Step 2b: Block ends at offset {idx_end}")

old_block = content[idx_start:idx_end]
print(f"Step 2c: Old block = {len(old_block)} chars")
print(f" Old head: {repr(old_block[:60])}")
print(f" Old tail: {repr(old_block[-60:])}")

# ── Sanity checks ─────────────────────────────────────────────────────────────
checks_before = {
    "CreditStore present": "CreditStore().add_credits" in old_block,
    "not already patched": "is_trialing" not in old_block,
    "credits_provisioned present": "credits_provisioned = credits" in old_block,
    "BLOCK_END verified": content[idx_end:idx_end + len(BLOCK_END_MARKER)] == BLOCK_END_MARKER,
}
for k, v in checks_before.items():
    print(f" [{('PASS' if v else 'FAIL')}] {k}")
if not all(checks_before.values()):
    sys.exit(f"Block validation failed: {checks_before}")

# ── Phase 3: build new block ──────────────────────────────────────────────────
# VERIFIED indentation from the actual file:
# S8  = 8 spaces  — 'if customer_id and price_id:' (1 space from function-level)
# S12 = 12 spaces — top-level statements inside the if block
# S16 = 16 spaces — inner if/for bodies
# S20 = 20 spaces — deeper nesting
# S24 = 24 spaces — CreditStore/logger close, tenant_id assignment
# S28 = 28 spaces — fn call continuations (logger args, CreditStore kwargs)

S8  = " " * 8
S12 = " " * 12
S16 = " " * 16
S20 = " " * 20
S24 = " " * 24
S28 = " " * 28

print(f" Indentation: S8={8} S12={12} S16={16} S20={20} S24={24} S28={28}")

new_block = (
    # Block start (S8 = 8 spaces — matches actual file)
    f"{S8}if customer_id and price_id:\n"
    "\n"

    # ── Trial detection ──────────────────────────────────────────────────
    f'{S12}is_trialing = (subscription.get("status") or "").lower() == "trialing"\n'
    "\n"

    # ── Tier resolution ──────────────────────────────────────────────────
    f"{S12}# Resolve tier from price_id via mapping\n"
    f"{S12}price_to_tier = get_tier_to_role_mapping()\n"
    f"{S12}tier_key = None\n"
    f"{S12}for pid, tk in price_to_tier.items():\n"
    f"{S16}if pid == price_id:\n"
    f"{S20}tier_key = tk\n"
    f"{S20}break\n"
    "\n"

    # ── Trial/tier credit resolution ─────────────────────────────────────
    f"{S12}if is_trialing:\n"
    f'{S16}tier_key = "trial"\n'
    f'{S16}credits = tier_credits("trial")\n'
    f"{S12}elif tier_key:\n"
    f'{S16}credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    f"{S12}else:\n"
    f"{S16}credits = 0\n"
    "\n"

    # ── Resolve tenant_id via customer email ─────────────────────────────
    f"{S12}# Find tenant_id from the customer's email\n"
    f"{S12}customer = await stripe_service._get_customer_by_id(customer_id)\n"
    f"{S12}if customer:\n"
    f"{S16}user_repo = UserRepository()\n"
    f"{S16}user = await user_repo.find_by_email(customer.email)\n"
    f"{S16}if user:\n"
    f"{S20}tenant_id = str(user.id)\n"
    "\n"

    # ── Persist trial dates in license metadata ──────────────────────────
    f"{S12}# Store trial start/end dates in license when trial starts\n"
    f'{S12}if is_trialing and event_type in (\n'
    f'{S16}"customer.subscription.created",\n'
    f'{S16}"customer.subscription.updated",\n'
    f"{S12}):\n"
    f"{S16}trial_dates = compute_trial_dates()\n"
    f"{S16}license_repo = LicenseRepository()\n"
    f"{S16}license_info = await license_repo.get_license_by_key(\n"
    f'{S28}user.license_key if hasattr(user, "license_key") else tenant_id\n'
    f"{S16})\n"
    f"{S16}if license_info:\n"
    f'{S24}meta = license_info.get("metadata") or {{}}\n'
    f'{S24}if not meta.get("trial_started_at"):\n'
    f"{S24}meta.update(trial_dates)\n"
    f'{S24}meta["trial_status"] = "trial"\n'
    f"{S24}await license_repo.update_license(\n"
    f'{S24}license_info["key_id"], {{"metadata": meta}}\n'
    f"{S24})\n"
    f"{S24}logger.info(\n"
    f'{S24}"Persisted trial dates for key %s: %s",\n'
    f'{S24}license_info.get("key_id"), trial_dates,\n'
    f"{S24})\n"
    "\n"

    # ── Trial deletion: defer to evaluator ───────────────────────────────
    f"{S12}# Defer trial subscription deletions to the evaluator (grace window)\n"
    f'{S12}if event_type == "customer.subscription.deleted" and is_trialing:\n'
    f"{S16}logger.info(\n"
    f'{S20}"Trial subscription deleted for %s - evaluator will handle grace window",\n'
    f"{S20}tenant_id,\n"
    f"{S16})\n"
    f"{S12}elif credits:\n"
    f"{S16}CreditStore().add_credits(\n"
    f"{S20}tenant_id=tenant_id,\n"
    f"{S20}amount=credits,\n"
    f'{S20}reason=f"stripe:{{event_type}}:{{event_id}}",\n'
    f"{S16})\n"
    f"{S16}credits_provisioned = credits\n"
    f"{S16}logger.info(\n"
    f'{S20}"Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    f"{S20}credits, tenant_id, tier_key, event_type,\n"
    f"{S16})\n"
)

print(f"Step 3: New block = {len(new_block)} chars (was {len(old_block)})")

# ── Phase 4: inject ──────────────────────────────────────────────────────────
new_content = content[:idx_start] + new_block + content[idx_end:]
print(f"Step 4: Total file = {len(new_content)} chars (was {len(content)})")

# ── Phase 5: write ──────────────────────────────────────────────────────────
with open(TARGET, "w") as f:
    f.write(new_content)
print("Step 5: Written to disk")

# ── Phase 6: syntax check ───────────────────────────────────────────────────
try:
    ast.parse(new_content)
    print("Step 6: Syntax OK")
except SyntaxError as e:
    print(f"\nSYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.msg}")
    ctx = new_content.split("\n")[max(0, e.lineno - 5):e.lineno + 3]
    for i, line in enumerate(ctx):
        spaces = len(line) - len(line.lstrip(" "))
        print(f" {max(1, e.lineno - 5 + i + 1)} S{spaces:2d}: {repr(line)}")
    sys.exit(1)

# ── Phase 7: symbol checks ──────────────────────────────────────────────────
checks_after = {
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
for k, v in checks_after.items():
    print(f" [{'PASS' if v else 'FAIL'}] {k}")

passing = sum(checks_after.values())
total = len(checks_after)
print(f"\nChecks: {passing}/{total} PASS")
if not all(checks_after.values()):
    failed = [k for k, v in checks_after.items() if not v]
    sys.exit(f"FAIL: {failed}")
print("All checks PASS — trial logic wired in")

# ── Phase 8: visual indentation check ────────────────────────────────────────
lines = new_content.split('\n')
idx_s = new_content.find('if customer_id and price_id:')
block_start_line = new_content[:idx_s].count('\n')
print(f"\nIndentation audit of patched block (line {block_start_line+1}):")
for i in range(block_start_line, block_start_line + 80):
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
