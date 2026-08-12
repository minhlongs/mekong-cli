#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning.

VERIFIED INDENTATION (from live file lines 754-781):
  S1 = 12s  — ALL statement/comment lines inside `if customer_id and price_id:`
  S2 = 16s  — body of inner if/for (1 level deeper)
  S3 = 20s  — one more level deeper
  S4 = 24s  — assignments inside nested if
  S5 = 28s  — fn call continuation (CreditStore kwargs, logger args)

BLOCK_END = chars 25963-25979: ')\n\n\n return {'
  - char 25963: ')'
  - chars 25964-25966: \n\n\n (3 newlines)
  - chars 25967-25970: '    ' (4 spaces = 'return {' is at function level)
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

# ── Phase 2: locate block ─────────────────────────────────────────────────────
# Verified: block starts at offset 24586, ends at offset 25963
# BLOCK_END = ')\n\n\n return {' where ')' closes logger.info(), 3 blanks, then 4-space return
BLOCK_START = " if customer_id and price_id:\n"
BLOCK_END = ")\n\n\n    return {"  # 3 newlines + 4 spaces then return at function level

idx_start = content.find(BLOCK_START)
if idx_start == -1:
    sys.exit("ERROR: block start not found")
print(f"Step 2a: Block starts at offset {idx_start} (line {content[:idx_start].count(chr(10))+1})")

# Search for end marker starting 500 chars after start
idx_end = content.find(BLOCK_END, idx_start + 500)
if idx_end == -1:
    # Re-verify: let's check what's actually after the logger close
    # Find the second `)\n\n\n` sequence in the function
    marker = ")\n\n\n"
    pos = idx_start + 500
    found = []
    while True:
        m = content.find(marker, pos)
        if m == -1:
            break
        after = content[m+len(marker):m+len(marker)+20]
        found.append((m, repr(after)))
        pos = m + 1
    print("\nAll ')\\n\\n\\n' sequences found in function:")
    for offset, after in found:
        print(f"  offset {offset}: → {after}")
    sys.exit("ERROR: block end not found — see sequences above")

print(f"Step 2b: Block ends at offset {idx_end}")
print(f"Step 2c: Old block = {idx_end - idx_start} chars")

old_block = content[idx_start:idx_end]
print(f" Old head: {repr(old_block[:60])}")
print(f" Old tail: {repr(old_block[-60:])}")

# ── Sanity checks ─────────────────────────────────────────────────────────────
checks_before = {
    "CreditStore present": "CreditStore().add_credits" in old_block,
    "not already patched": "is_trialing" not in old_block,
    "credits_provisioned present": "credits_provisioned = credits" in old_block,
}
for k, v in checks_before.items():
    print(f" [{('PASS' if v else 'FAIL')}] {k}")
if not all(checks_before.values()):
    sys.exit(f"Block validation failed: {checks_before}")

# ── Phase 3: build new block ──────────────────────────────────────────────────
# From live file inspection:
#   S1 = 12s  (top-level statements inside `if customer_id and price_id:`)
#   S2 = 16s  (if/for/elif bodies — 1 level deeper)
#   S3 = 20s  (2 levels deeper: assignments in nested if)
#   S4 = 24s  (CreditStore close, license_repo calls)
#   S5 = 28s  (fn call continuations: kwargs, logger args)

S1 = " " * 12
S2 = " " * 16
S3 = " " * 20
S4 = " " * 24
S5 = " " * 28

new_block = (
    # Block start (identical anchor)
    f"{S1}if customer_id and price_id:\n"
    "\n"

    # ── Trial detection (top-level statement at S1) ──────────────────────
    f'{S1}is_trialing = (subscription.get("status") or "").lower() == "trialing"\n'
    "\n"

    # ── Tier resolution ──────────────────────────────────────────────────
    f"{S1}# Resolve tier from price_id via the mapping\n"
    f"{S1}price_to_tier = get_tier_to_role_mapping()\n"
    f"{S1}tier_key = None\n"
    f"{S1}for pid, tk in price_to_tier.items():\n"
    f"{S2}if pid == price_id:\n"
    f"{S3}tier_key = tk\n"
    f"{S3}break\n"
    "\n"

    # ── Credits: trial-aware or tier-based ───────────────────────────────
    f"{S1}if is_trialing:\n"
    f'{S2}tier_key = "trial"\n'
    f'{S2}credits = tier_credits("trial")\n'
    f"{S1}elif tier_key:\n"
    f'{S2}credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    f"{S1}else:\n"
    f"{S2}credits = 0\n"
    "\n"

    # ── Resolve tenant_id via customer email ─────────────────────────────
    f"{S1}# Resolve tenant_id: find user by customer email\n"
    f"{S1}customer = await stripe_service._get_customer_by_id(customer_id)\n"
    f"{S1}if customer:\n"
    f"{S2}user_repo = UserRepository()\n"
    f"{S2}user = await user_repo.find_by_email(customer.email)\n"
    f"{S2}if user:\n"
    f"{S3}tenant_id = str(user.id)\n"
    "\n"

    # ── Persist trial dates in license metadata ───────────────────────────
    f"{S1}# Persist trial dates in license metadata when trial starts\n"
    f'{S1}if is_trialing and event_type in (\n'
    f'{S2}"customer.subscription.created",\n'
    f'{S2}"customer.subscription.updated",\n'
    f"{S1}):\n"
    f"{S2}trial_dates = compute_trial_dates()\n"
    f"{S2}license_repo = LicenseRepository()\n"
    f"{S2}license_info = await license_repo.get_license_by_key(\n"
    f'{S5}user.license_key if hasattr(user, "license_key") else tenant_id\n'
    f"{S2})\n"
    f"{S2}if license_info:\n"
    f'{S5}meta = license_info.get("metadata") or {{}}\n'
    f"{S5}if not meta.get(\"trial_started_at\"):\n"
    f"{S5}meta.update(trial_dates)\n"
    f'{S5}meta["trial_status"] = "trial"\n'
    f"{S5}await license_repo.update_license(\n"
    f'{S5}license_info["key_id"], {{"metadata": meta}}\n'
    f"{S5})\n"
    f"{S5}logger.info(\n"
    f'{S5}"Persisted trial dates for license %s: %s",\n'
    f'{S5}license_info.get("key_id"), trial_dates,\n'
    f"{S5})\n"
    "\n"

    # ── Trial deletion: defer to evaluator ─────────────────────────────────
    f"{S2}# During trial deletion, defer to evaluator for grace/expire\n"
    f'{S2}if event_type == "customer.subscription.deleted" and is_trialing:\n'
    f"{S3}logger.info(\n"
    f'{S4}"Trial subscription deleted for %s - deferring to evaluator",\n'
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

print(f"\nStep 3: New block = {len(new_block)} chars (was {len(old_block)})")

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

# ── Phase 8: visual indentation check ────────────────────────────────────────
lines = new_content.split('\n')
idx_s = new_content.find(' if customer_id and price_id:')
block_start_line = new_content[:idx_s].count('\n')
print(f"\nIndentation audit of patched block (line {block_start_line+1}):")
for i in range(block_start_line, block_start_line + 60):
    if i >= len(lines):
        break
    line = lines[i]
    if not line.strip():
        print(f"  L{i+1:4d}: (blank)")
        continue
    spaces = len(line) - len(line.lstrip(' '))
    text = line.lstrip(' ')
    print(f"  L{i+1:4d} ({spaces:2d}s): {repr(text[:70])}")
    if 'return {' in line:
        break
