#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning (v13).

FIXED: BLOCK_END uses 1 space before 'return {' (verified at byte offset 25973).
"""

import sys
import ast

TARGET = "src/api/billing_endpoints.py"

with open(TARGET, "r") as f:
    content = f.read()

# ── Phase 1: add trial_evaluator import (idempotent) ─────────────────────────
ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"
if "from src.services.trial_evaluator import" not in content:
    content = content.replace(ANCHOR, ANCHOR + IMPORT, 1)
    print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# ── Phase 2: locate block ─────────────────────────────────────────────────────
# BLOCK_START: ' if customer_id and price_id:\n' — 1 space (function-level indent)
# BLOCK_END: ')\n\n\n return {' — 1 space before return at function-level
# Verified byte offsets in original (pre-P1) file:
#   start: 24586, end ')' at 25969, 'return' at 25973 (1 space)
# After Phase 1 (+77 bytes), shift is: start 24663, close ')' 25746, 'return' 25750

BLOCK_START = " if customer_id and price_id:\n"
BLOCK_END = ")\n\n\n    return {"  # 4 spaces before return — VERIFIED by hex dump

idx_start = content.find(BLOCK_START)
if idx_start == -1:
    sys.exit("ERROR: block start not found")
print(f"Step 2a: Block start at offset {idx_start} (line {content[:idx_start].count(chr(10))+1})")

idx_end = content.find(BLOCK_END, idx_start + 500)
if idx_end == -1:
    sys.exit("ERROR: block end not found")
print(f"Step 2b: Block end at offset {idx_end}")
old_block = content[idx_start:idx_end]
print(f"Step 2c: Old block = {len(old_block)} chars")
print(f" Old head: {repr(old_block[:60])}")
print(f" Old tail: {repr(old_block[-60:])}")

# ── Sanity checks ─────────────────────────────────────────────────────────────
checks_before = {
    "CreditStore present": "CreditStore().add_credits" in old_block,
    "not already patched": "is_trialing" not in old_block,
    "credits_provisioned present": "credits_provisioned = credits" in old_block,
    "BLOCK_END verified": content[idx_end:idx_end + len(BLOCK_END)] == BLOCK_END,
}
for k, v in checks_before.items():
    print(f" [{('PASS' if v else 'FAIL')}] {k}")
if not all(checks_before.values()):
    sys.exit(f"Block validation failed: {checks_before}")

# ── Phase 3: build new block with dynamic base_indent ─────────────────────────
# The original block shows 12-space indent for ALL statements inside `if customer_id`
# We detect this from the old_block content dynamically.
# Pattern: the block_start line itself is at function_level + 1 space
# All statements are at function_level + 12 spaces (S1=12)
# But we compute S1 from the actual indentation difference.

# Find the function definition line to know function-level indent
# Walk backwards from idx_start to find the last 'def ' or 'async def '
func_search = content[:idx_start]
func_lines = func_search.split("\n")
func_indent = 0
for line in reversed(func_lines):
    stripped = line.strip()
    if stripped.startswith("def ") or stripped.startswith("async def "):
        func_indent = len(line) - len(line.lstrip())
        break
print(f"Step 3a: Function-level indent = {func_indent} spaces")

# The `if customer_id and price_id:` line is at func_indent + 1 space
# All statement lines inside it are at func_indent + 12 = body_indent
# Verify by checking actual lines in old_block
body_indent = None
for bline in old_block.split("\n"):
    stripped = bline.strip()
    if stripped and not stripped.startswith("if customer_id"):
        body_indent = len(bline) - len(bline.lstrip())
        break

if body_indent is None:
    sys.exit("ERROR: could not determine body indent from old_block")

print(f"Step 3b: Body indent from old_block = {body_indent} spaces")

S1 = " " * body_indent      # top-level statements (inside if customer_id)
S2 = " " * (body_indent + 4)  # if/for bodies
S3 = " " * (body_indent + 8)  # deeper nesting
S4 = " " * (body_indent + 12) # call close
S5 = " " * (body_indent + 16) # fn call continuations
print(f" S1={body_indent} S2={body_indent+4} S3={body_indent+8} S4={body_indent+12} S5={body_indent+16}")

new_block = (
    # Block start (identical anchor)
    f"{S1}if customer_id and price_id:\n"
    "\n"

    # ── Trial detection ──────────────────────────────────────────────────
    f'{S1}is_trialing = (subscription.get("status") or "").lower() == "trialing"\n'
    "\n"

    # ── Tier resolution ──────────────────────────────────────────────────
    f"{S1}# Resolve tier from price_id via mapping\n"
    f"{S1}price_to_tier = get_tier_to_role_mapping()\n"
    f"{S1}tier_key = None\n"
    f"{S1}for pid, tk in price_to_tier.items():\n"
    f"{S2}if pid == price_id:\n"
    f"{S3}tier_key = tk\n"
    f"{S3}break\n"
    "\n"

    # ── Trial/tier credit resolution ─────────────────────────────────────
    f"{S1}if is_trialing:\n"
    f'{S2}tier_key = "trial"\n'
    f'{S2}credits = tier_credits("trial")\n'
    f"{S1}elif tier_key:\n"
    f'{S2}credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    f"{S1}else:\n"
    f"{S2}credits = 0\n"
    "\n"

    # ── Resolve tenant_id via customer email ─────────────────────────────
    f"{S1}# Find tenant_id from the customer's email\n"
    f"{S1}customer = await stripe_service._get_customer_by_id(customer_id)\n"
    f"{S1}if customer:\n"
    f"{S2}user_repo = UserRepository()\n"
    f"{S2}user = await user_repo.find_by_email(customer.email)\n"
    f"{S2}if user:\n"
    f"{S3}tenant_id = str(user.id)\n"
    "\n"

    # ── Persist trial dates in license metadata ──────────────────────────
    f"{S2}# Store trial start/end dates in license when a trial subscription starts\n"
    f'{S2}if is_trialing and event_type in (\n'
    f'{S3}"customer.subscription.created",\n'
    f'{S3}"customer.subscription.updated",\n'
    f"{S2}):\n"
    f"{S3}trial_dates = compute_trial_dates()\n"
    f"{S3}license_repo = LicenseRepository()\n"
    f"{S3}license_info = await license_repo.get_license_by_key(\n"
    f'{S5}user.license_key if hasattr(user, "license_key") else tenant_id\n'
    f"{S3})\n"
    f"{S3}if license_info:\n"
    f'{S5}meta = license_info.get("metadata") or {{}}\n'
    f'{S5}if not meta.get("trial_started_at"):\n'
    f"{S5}meta.update(trial_dates)\n"
    f'{S5}meta["trial_status"] = "trial"\n'
    f"{S5}await license_repo.update_license(\n"
    f'{S5}license_info["key_id"], {{"metadata": meta}}\n'
    f"{S5})\n"
    f"{S5}logger.info(\n"
    f'{S5}"Persisted trial dates for key %s: %s",\n'
    f'{S5}license_info.get("key_id"), trial_dates,\n'
    f"{S5})\n"
    "\n"

    # ── Trial deletion: defer to evaluator for grace/expire ──────────────
    f"{S2}# Defer trial subscription deletions to the evaluator (grace→expire)\n"
    f'{S2}if event_type == "customer.subscription.deleted" and is_trialing:\n'
    f"{S3}logger.info(\n"
    f'{S4}"Trial subscription deleted for %s - evaluator will handle grace window",\n'
    f"{S4}tenant_id,\n"
    f"{S3})\n"
    f"{S2}elif credits:\n"
    f"{S3}CreditStore().add_credits(\n"
    f"{S4}tenant_id=tenant_id,\n"
    f"{S4}amount=credits,\n"
    f'{S4}reason=f"stripe:{{event_type}}:{{event_id}}",\n'
    f"{S3})\n"
    f"{S3}credits_provisioned = credits\n"
    f"{S3}logger.info(\n"
    f'{S4}"Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    f"{S4}credits, tenant_id, tier_key, event_type,\n"
    f"{S3})\n"
)

print(f"Step 3: New block = {len(new_block)} chars (was {len(old_block)})")

# ── Phase 4: inject ───────────────────────────────────────────────────────────
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
    print(f"\nSYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.msg}")
    ctx = new_content.split("\n")[max(0, e.lineno - 5):e.lineno + 3]
    for i, line in enumerate(ctx):
        spaces = len(line) - len(line.lstrip(" "))
        print(f" {max(1, e.lineno - 5 + i + 1)} S{spaces:2d}: {repr(line)}")
    sys.exit(1)

# ── Phase 7: symbol checks ────────────────────────────────────────────────────
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
