#!/usr/bin/env python3
"""Apply trial-aware patch to billing_endpoints.py

Strategy:
 1. Add trial_evaluator import if missing (check original content)
 2. Find the target block by unique start marker + end marker
 3. Build new block by transforming the extracted bytes
 4. Replace + write + verify
"""
import ast
import sys

TARGET = "src/api/billing_endpoints.py"

with open(TARGET, "rb") as f:
    raw = f.read()

errors = []
text = raw.decode("utf-8")

# ── Step 1: import ─────────────────────────────────────────────────────────────
IMPORT_ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT_LINE   = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"

if IMPORT_LINE not in text:
    if IMPORT_ANCHOR not in text:
        errors.append("Cannot find CreditStore import anchor")
    else:
        text = text.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_LINE, 1)
        raw = text.encode("utf-8")
        print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# ── Step 2: locate block ───────────────────────────────────────────────────────
BLOCK_START = " if customer_id and price_id:"
BLOCK_END   = ")\n\n\nreturn {\n \"status\""

i_start = text.find(BLOCK_START)
if i_start == -1:
    sys.exit("ERROR: cannot find block start marker")

i_end = text.find(BLOCK_END, i_start + 100)
if i_end == -1:
    sys.exit("ERROR: cannot find block end marker")

old_block = text[i_start:i_end]
print(f"Step 2: Found block {len(old_block)} chars at offset {i_start}")

# ── Step 2b: guard against double-patch ────────────────────────────────────────
if "is_trialing" in old_block:
    sys.exit("Block already has trial logic — aborting (file may already be patched)")

# ── Step 2c: build new block ───────────────────────────────────────────────────
# Replace the tier_key-only logic with trial-aware logic
# Strategy: inject is_trialing detection before tier_key resolution,
#           add license metadata persistence before credit provisioning,
#           wrap credit provisioning with trial-delete guard.

new_block = old_block  # start from original, then do targeted replacements

# 1) After "# Resolve tier from price_id via the mapping", add price_to_tier + tier_key init
#    (original only has get_tier_to_role_mapping() then direct tier_key lookup)
old_tier_resolve = '# Resolve tier from price_id via the mapping\n price_to_tier = get_tier_to_role_mapping()\n # Invert: price_id → tier_key\n tier_key = None\n for pid, tk in price_to_tier.items():\n  if pid == price_id:\n   tier_key = tk\n   break\n'
new_tier_resolve = '# Resolve tier from price_id via the mapping\n price_to_tier = get_tier_to_role_mapping()\n tier_key = None\n for pid, tk in price_to_tier.items():\n  if pid == price_id:\n   tier_key = tk\n   break\n'
new_block = new_block.replace(old_tier_resolve, new_tier_resolve)

# 2) After " if customer_id and price_id:\n", inject is_trialing detection
new_block = new_block.replace(
    " if customer_id and price_id:\n",
    " if customer_id and price_id:\n"
    " is_trialing = (subscription.get(\"status\") or \"\").lower() == \"trialing\"\n",
    1
)

# 3) Replace " if tier_key:\n  credits = ... else 0\n" with trial-aware credits
old_credits = ' if tier_key:\n  credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
new_credits = (
    ' if is_trialing:\n'
    '  tier_key = "trial"\n'
    '  credits = tier_credits("trial")\n'
    ' elif tier_key:\n'
    '  credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    ' else:\n'
    '  credits = 0\n'
)
new_block = new_block.replace(old_credits, new_credits)

# 4) Change "Resolve tenant_id: find user" comment to "Resolve tenant_id + user"
new_block = new_block.replace(
    "# Resolve tenant_id: find user by customer email\n",
    "# Resolve tenant_id + user\n"
)

# 5) Replace CreditStore.add_credits + credits_provisioned + logger.info block
#    with trial-aware version + license metadata persistence
old_provision = (
    ' CreditStore().add_credits(\n'
    '  tenant_id=tenant_id,\n'
    '  amount=credits,\n'
    '  reason=f"stripe:{event_type}:{event_id}",\n'
    ' )\n'
    ' credits_provisioned = credits\n'
    ' logger.info(\n'
    '  "Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    '  credits, tenant_id, tier_key, event_type,\n'
    ' )\n'
)

new_provision = (
    '# Persist trial dates in license metadata when trial starts\n'
    ' if is_trialing and event_type in (\n'
    '  "customer.subscription.created",\n'
    '  "customer.subscription.updated",\n'
    ' ):\n'
    '  trial_dates = compute_trial_dates()\n'
    '  license_repo = LicenseRepository()\n'
    '  license_info = await license_repo.get_license_by_key(\n'
    '   user.license_key if hasattr(user, "license_key") else tenant_id\n'
    '  )\n'
    '  if license_info:\n'
    '   meta = license_info.get("metadata") or {}\n'
    '   if not meta.get("trial_started_at"):\n'
    '    meta.update(trial_dates)\n'
    '    meta["trial_status"] = "trial"\n'
    '   await license_repo.update_license(\n'
    '    license_info["key_id"], {"metadata": meta}\n'
    '   )\n'
    '   logger.info(\n'
    '    "Persisted trial dates for license %s: %s",\n'
    '    license_info.get("key_id"), trial_dates,\n'
    '   )\n'
    '\n'
    '# During trial deletion, defer to evaluator for grace/expire\n'
    ' if event_type == "customer.subscription.deleted" and is_trialing:\n'
    '  logger.info(\n'
    '   "Trial subscription deleted for %s - deferring to evaluator",\n'
    '   tenant_id,\n'
    '  )\n'
    ' elif credits:\n'
    '  CreditStore().add_credits(\n'
    '   tenant_id=tenant_id,\n'
    '   amount=credits,\n'
    '   reason=f"stripe:{event_type}:{event_id}",\n'
    '  )\n'
    '  credits_provisioned = credits\n'
    '  logger.info(\n'
    '   "Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    '   credits, tenant_id, tier_key, event_type,\n'
    '  )\n'
)

new_block = new_block.replace(old_provision, new_provision)

# ── Assemble + write ───────────────────────────────────────────────────────────
new_text = text[:i_start] + new_block + text[i_end:]
raw = new_text.encode("utf-8")

with open(TARGET, "wb") as f:
    f.write(raw)
print(f"Written: {len(raw)} bytes")

# ── Verify syntax ──────────────────────────────────────────────────────────────
try:
    ast.parse(new_text)
    print("Syntax: OK")
except SyntaxError as e:
    ctx = new_text.split("\n")[max(0, e.lineno - 5):e.lineno + 3]
    print(f"\nSYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.msg}")
    for i, line in enumerate(ctx):
        print(f"  {max(1,e.lineno-5+i)+1}: {repr(line)}")
    sys.exit(1)

# ── Symbol checks ──────────────────────────────────────────────────────────────
checks = {
    "is_trialing":            "is_trialing" in new_text,
    "compute_trial_dates":    "compute_trial_dates" in new_text,
    "evaluate_trial":         "evaluate_trial" in new_text,
    "trial_status":           '"trial_status"' in new_text,
    "LicenseRepository":      "LicenseRepository" in new_text,
    "trial_started_at":       "trial_started_at" in new_text,
    "deferring to evaluator": "deferring to evaluator" in new_text,
    "trial_evaluator import": "from src.services.trial_evaluator import" in new_text,
    "trial subscription deleted": "Trial subscription deleted" in new_text,
}
for k, v in checks.items():
    status = "PASS" if v else "FAIL"
    print(f"  [{status}] {k}")

if all(checks.values()):
    print("\nAll checks PASS")
else:
    print(f"\nFAIL: {[k for k,v in checks.items() if not v]}")
    sys.exit(1)
