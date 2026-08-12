#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning (v15).

STRATEGY: Find block on clean file (original offsets), modify block,
THEN add import (Phase 1 last, since import position is INSIDE the block).

Hex-dump verified offsets on clean file:
  offset 24587 (24580+7 bytes): "        if customer_id and price_id:\n"  S8
  offset 25964: "        )\n\n\n    return {\n"  S4 return
"""

import sys
import ast

TARGET = "src/api/billing_endpoints.py"

with open(TARGET, "r") as f:
    content = f.read()

# ── Phase 0: verify clean state ───────────────────────────────────────────────
if "is_trialing" in content:
    sys.exit("ERROR: file not clean — run 'git checkout -- src/api/billing_endpoints.py' first")
print("Step 0: Clean state verified")

# ── Phase 1: locate block ────────────────────────────────────────────────────
# Verified byte offsets from hex dump on clean file:
#   24587: 8 spaces + "if customer_id and price_id:\n"
#   25964: 8 spaces + ")" then \n\n\n then 4 spaces + "return {\n"

BLOCK_START_RAW = "        if customer_id and price_id:\n"   # S8
BLOCK_END_RAW   = "\n\n\n    return {\n"                      # 3x\n + S4

idx_start = content.find(BLOCK_START_RAW)
if idx_start == -1:
    sys.exit("ERROR: block start not found")
print(f"Step 1a: Block start offset {idx_start} (line {content[:idx_start].count(chr(10))+1})")

idx_end = content.find(BLOCK_END_RAW, idx_start + 500)
if idx_end == -1:
    sys.exit("ERROR: block end not found")
print(f"Step 1b: Block end offset {idx_end}")

old_block = content[idx_start:idx_end]
print(f"Step 1c: Old block = {len(old_block)} chars")
print(f" Head: {repr(old_block[:60])}")
print(f" Tail: {repr(old_block[-60:])}")

checks_before = {
    "CreditStore present": "CreditStore().add_credits" in old_block,
    "not already patched": "is_trialing" not in old_block,
    "credits_provisioned": "credits_provisioned = credits" in old_block,
}
for k, v in checks_before.items():
    print(f" [{('PASS' if v else 'FAIL')}] {k}")
if not all(checks_before.values()):
    sys.exit(f"Block validation failed: {checks_before}")

# ── Phase 2: build new block ─────────────────────────────────────────────────
# Indentation ladder (verified from old_block):
# S4  = 4 spaces  — "return {" at function level
# S8  = 8 spaces  — "if customer_id and price_id:" anchor (the if itself)
# S12 = 12 spaces — body of if customer_id block (S8 + 4)
# S16 = 16 spaces — body of inner if/for (S12 + 4)
# S20 = 20 spaces — assignments inside inner if (S16 + 4)
# S24 = 24 spaces — body of if license_info (S20 + 4)
# S28 = 28 spaces — deepest nesting (S24 + 4)

S4  = " " * 4
S8  = " " * 8
S12 = " " * 12
S16 = " " * 16
S20 = " " * 20
S24 = " " * 24
S28 = " " * 28

print(f" Indentation: S4={4} S8={8} S12={12} S16={16} S20={20} S24={24} S28={28}")

new_block = (
    # ── Anchor (S8) ──────────────────────────────────────────────────────────
    f"{S8}if customer_id and price_id:\n"
    "\n"

    # ── Trial detection (S12 = 1 level inside if) ───────────────────────────
    f'{S12}is_trialing = (subscription.get("status") or "").lower() == "trialing"\n'
    "\n"

    # ── Tier resolution (S12 for top, S16 for inner, S20 for assign) ────────
    f"{S12}# Resolve tier from price_id via mapping\n"
    f"{S12}price_to_tier = get_tier_to_role_mapping()\n"
    f"{S12}tier_key = None\n"
    f"{S12}for pid, tk in price_to_tier.items():\n"
    f"{S16}if pid == price_id:\n"
    f"{S20}tier_key = tk\n"
    f"{S20}break\n"
    "\n"

    # ── Credit resolution (S12 / S16) ───────────────────────────────────────
    f"{S12}if is_trialing:\n"
    f'{S16}tier_key = "trial"\n'
    f'{S16}credits = tier_credits("trial")\n'
    f"{S12}elif tier_key:\n"
    f'{S16}credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    f"{S12}else:\n"
    f"{S16}credits = 0\n"
    "\n"

    # ── Resolve tenant_id (S12 → S16 → S20) ────────────────────────────────
    f"{S12}# Find tenant_id from the customer's email\n"
    f"{S12}customer = await stripe_service._get_customer_by_id(customer_id)\n"
    f"{S12}if customer:\n"
    f"{S16}user_repo = UserRepository()\n"
    f"{S16}user = await user_repo.find_by_email(customer.email)\n"
    f"{S16}if user:\n"
    f"{S20}tenant_id = str(user.id)\n"
    "\n"

    # ── Persist trial dates in license metadata ──────────────────────────────
    # Structure:
    #   S12:  if is_trialing and event_type in (...):
    #   S16:      trial_dates = ...
    #   S16:      license_info = await ...  (call continuation to S28)
    #   S16:      if license_info:
    #   S24:          meta = ...
    #   S24:          if not meta.get("trial_started_at"):
    #   S28:              meta.update(...)     ← body of innermost if
    #   S28:              meta["trial_status"] = ...
    #   S28:              await license_repo.update_license(...)
    #   S28:              logger.info(...)      ← body of innermost if

    f"{S12}# Store trial start/end dates in license when trial starts\n"
    f"{S12}if is_trialing and event_type in (\n"
    f'{S16}"customer.subscription.created",\n'
    f'{S16}"customer.subscription.updated",\n'
    f"{S12}):\n"
    # ── Inside `if is_trialing and event_type in (...)` → S16 ───────────────
    f"{S16}trial_dates = compute_trial_dates()\n"
    f"{S16}license_repo = LicenseRepository()\n"
    f"{S16}license_info = await license_repo.get_license_by_key(\n"
    f'{S28}user.license_key if hasattr(user, "license_key") else tenant_id\n'
    f"{S16})\n"
    f"{S16}if license_info:\n"
    # ── Inside `if license_info:` → S24 ─────────────────────────────────────
    f'{S24}meta = license_info.get("metadata") or {{}}\n'
    f"{S24}if not meta.get(\"trial_started_at\"):\n"
    # ── Inside `if not meta.get("trial_started_at"):` → S28 ────────────────
    f"{S28}meta.update(trial_dates)\n"
    f'{S28}meta["trial_status"] = "trial"\n'
    f"{S28}await license_repo.update_license(\n"
    f'{S28}license_info["key_id"], {{"metadata": meta}}\n'
    f"{S28})\n"
    f"{S28}logger.info(\n"
    f'{S28}"Persisted trial dates for key %s: %s",\n'
    f'{S28}license_info.get("key_id"), trial_dates,\n'
    f"{S28})\n"
    "\n"

    # ── Trial deletion: defer to evaluator ──────────────────────────────────
    # Structure:
    #   S12:  # comment
    #   S12:  if event_type == "customer.subscription.deleted" and is_trialing:
    #   S16:      evaluate_trial(tenant_id, customer_id)
    #   S16:      logger.info(...)
    #   S20:          ... args ...
    #   S16:  elif credits:
    #   S16:      CreditStore().add_credits(...)
    #   S20:          ... kwargs ...       ← S20 = S16 + 4
    #   S16:      credits_provisioned = credits
    #   S16:      logger.info(...)
    #   S20:          arg1,

    f"{S12}# Defer trial subscription deletions to the evaluator (grace window)\n"
    f'{S12}if event_type == "customer.subscription.deleted" and is_trialing:\n'
    # ── Inside deletion guard → S16 ──────────────────────────────────────────
    f"{S16}evaluate_trial(tenant_id, customer_id)\n"
    f"{S16}logger.info(\n"
    f'{S24}"Trial subscription deleted for %s — evaluator will handle grace window",\n'
    f"{S24}tenant_id,\n"
    f"{S16})\n"
    f"{S12}elif credits:\n"
    # ── Inside elif credits → S16 ────────────────────────────────────────────
    f"{S16}CreditStore().add_credits(\n"
    # kwargs → S20
    f"{S20}tenant_id=tenant_id,\n"
    f"{S20}amount=credits,\n"
    f'{S28}reason=f"stripe:{{event_type}}:{{event_id}}",\n'
    f"{S16})\n"
    f"{S16}credits_provisioned = credits\n"
    f"{S16}logger.info(\n"
    f'{S24}"Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    f"{S24}credits, tenant_id, tier_key, event_type,\n"
    f"{S16})\n"
)

print(f"Step 2: New block = {len(new_block)} chars (was {len(old_block)})")

# ── Phase 3: inject block first (before import) ───────────────────────────────
new_content = content[:idx_start] + new_block + content[idx_end:]
print(f"Step 3: File after block patch = {len(new_content)} chars")

# ── Phase 4: add import (now that block is patched, find new CreditStore pos) ─
ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"
if "from src.services.trial_evaluator import" not in new_content:
    new_content = new_content.replace(ANCHOR, ANCHOR + IMPORT, 1)
    print("Step 4: Added trial_evaluator import (77 bytes)")
else:
    print("Step 4: Import already present")

print(f"Step 4b: Final file = {len(new_content)} chars")

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
checks = {
    "is_trialing": "is_trialing" in new_content,
    "compute_trial_dates": "compute_trial_dates" in new_content,
    "evaluate_trial": "evaluate_trial" in new_content,
    "trial_status": '"trial_status"' in new_content,
    "LicenseRepository": "LicenseRepository()" in new_content,
    "trial_started_at": '"trial_started_at"' in new_content,
    "evaluator deferral": "evaluator will handle grace window" in new_content,
    "trial_evaluator import": "from src.services.trial_evaluator import" in new_content,
    'subscription.get("status")': 'subscription.get("status")' in new_content,
    "customer.subscription.deleted": "customer.subscription.deleted" in new_content,
    "CreditStore preserved": "CreditStore().add_credits" in new_content,
    "tier_credits preserved": "tier_credits(" in new_content,
    "return { preserved": "    return {" in new_content,
    "credits_provisioned preserved": "credits_provisioned = credits" in new_content,
    "trial_started_at check": 'meta.get("trial_started_at")' in new_content,
    "meta.update call": "meta.update(trial_dates)" in new_content,
    "update_license call": "update_license(" in new_content,
}
for k, v in checks.items():
    print(f" [{'PASS' if v else 'FAIL'}] {k}")
passing = sum(checks.values())
print(f"\nChecks: {passing}/{len(checks)} PASS")
if not all(checks.values()):
    failed = [k for k, v in checks.items() if not v]
    sys.exit(f"FAIL: {failed}")
print("All checks PASS — trial logic wired in")

# ── Phase 8: visual indentation audit ─────────────────────────────────────────
lines = new_content.split('\n')
idx_s = new_content.find('if customer_id and price_id:')
bsl = new_content[:idx_s].count('\n')
print(f"\nIndentation audit (line {bsl+1}):")
for i in range(bsl, bsl + 90):
    if i >= len(lines):
        break
    line = lines[i]
    if not line.strip():
        print(f" L{i+1:4d}: (blank)")
        continue
    spaces = len(line) - len(line.lstrip(' '))
    text = line.lstrip(' ')
    print(f" L{i+1:4d} ({spaces:2d}s): {repr(text[:65])}")
    if 'return {' in line:
        break
print("\n=== PATCH COMPLETE ===")
