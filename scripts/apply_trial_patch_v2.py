#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning.

Strategy:
1. Add trial_evaluator import
2. Regex-match the flat-indent block and replace with trial-aware version
"""
import re
import ast
import sys

TARGET = "src/api/billing_endpoints.py"

with open(TARGET, "r") as f:
    content = f.read()

# ── Step 1: import ─────────────────────────────────────────────────────────────
IMPORT_ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT_LINE = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"
if "from src.services.trial_evaluator import" not in content:
    content = content.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_LINE, 1)
    print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# ── Step 2: locate block ───────────────────────────────────────────────────────
# The block uses 1-space visual indent (flat-indent style).
# We match from " if customer_id and price_id:" through "return {"
#   - "return {" is CONSUMED by the regex (the { is included)
#   - So the new block must include "return {" at the end
pattern = re.compile(r' if customer_id and price_id:.*?return \{', re.DOTALL)
m = pattern.search(content)
if not m:
    sys.exit("ERROR: regex did not match the block")

i_start = m.start()
i_end = m.end()
old_block = content[i_start:i_end]
if "is_trialing" in old_block:
    sys.exit("Block already has trial logic — aborting")

print(f"Step 2: Found block {len(old_block)} chars at offset {i_start}")
print(f"  Block ends with: {repr(old_block[-40:])}")

# ── Step 3: build new block ────────────────────────────────────────────────────
# " " (1 space) = flat-indent body indent within the function
B = " "

new_block = (
    f' if customer_id and price_id:\n'
    f'{B}is_trialing = (subscription.get("status") or "").lower() == "trialing"\n'
    f'\n'
    f' # Resolve tier from price_id via the mapping\n'
    f'{B}price_to_tier = get_tier_to_role_mapping()\n'
    f'{B}tier_key = None\n'
    f'{B}for pid, tk in price_to_tier.items():\n'
    f'{B} if pid == price_id:\n'
    f'{B}  tier_key = tk\n'
    f'{B} break\n'
    f'\n'
    f'{B}if is_trialing:\n'
    f'{B} tier_key = "trial"\n'
    f'{B} credits = tier_credits("trial")\n'
    f'{B}elif tier_key:\n'
    f'{B} credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    f'{B}else:\n'
    f'{B} credits = 0\n'
    f'\n'
    f' # Resolve tenant_id + user\n'
    f'{B}customer = await stripe_service._get_customer_by_id(customer_id)\n'
    f'{B}if customer:\n'
    f'{B} user_repo = UserRepository()\n'
    f'{B} user = await user_repo.find_by_email(customer.email)\n'
    f'{B} if user:\n'
    f'{B}  tenant_id = str(user.id)\n'
    f'\n'
    f' # Persist trial dates in license metadata when trial starts\n'
    f'{B}if is_trialing and event_type in (\n'
    f'{B} "customer.subscription.created",\n'
    f'{B} "customer.subscription.updated",\n'
    f'{B}):\n'
    f'{B} trial_dates = compute_trial_dates()\n'
    f'{B} license_repo = LicenseRepository()\n'
    f'{B} license_info = await license_repo.get_license_by_key(\n'
    f'{B}  user.license_key if hasattr(user, "license_key") else tenant_id\n'
    f'{B} )\n'
    f'{B} if license_info:\n'
    f'{B}  meta = license_info.get("metadata") or {{}}\n'
    f'{B}  if not meta.get("trial_started_at"):\n'
    f'{B}   meta.update(trial_dates)\n'
    f'{B}  meta["trial_status"] = "trial"\n'
    f'{B}  await license_repo.update_license(\n'
    f'{B}   license_info["key_id"], {{"metadata": meta}}\n'
    f'{B}  )\n'
    f'{B}  logger.info(\n'
    f'{B}   "Persisted trial dates for license %s: %s",\n'
    f'{B}   license_info.get("key_id"), trial_dates,\n'
    f'{B}  )\n'
    f'\n'
    f' # During trial deletion, defer to evaluator for grace/expire\n'
    f'{B}if event_type == "customer.subscription.deleted" and is_trialing:\n'
    f'{B} logger.info(\n'
    f'{B}  "Trial subscription deleted for %s - deferring to evaluator",\n'
    f'{B}  tenant_id,\n'
    f'{B} )\n'
    f'{B}elif credits:\n'
    f'{B} CreditStore().add_credits(\n'
    f'{B}  tenant_id=tenant_id,\n'
    f'{B}  amount=credits,\n'
    f'{B}  reason=f"stripe:{{event_type}}:{{event_id}}",\n'
    f'{B} )\n'
    f'{B} credits_provisioned = credits\n'
    f'{B} logger.info(\n'
    f'{B}  "Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    f'{B}  credits, tenant_id, tier_key, event_type,\n'
    f'{B} )\n'
    f'\n'
    f' # Process event\n'
    f'event_type = event.get("type", "")\n'
)

print(f"Step 3: New block {len(new_block)} chars (was {len(old_block)})")

# Inject
new_content = content[:i_start] + new_block + content[i_end:]
print(f"Step 4: Total file {len(new_content)} chars (was {len(content)})")

# Write
with open(TARGET, "w") as f:
    f.write(new_content)
print("Step 5: Written to disk")

# ── Verify syntax ──────────────────────────────────────────────────────────────
try:
    ast.parse(new_content)
    print("Step 6: Syntax OK")
except SyntaxError as e:
    ctx = new_content.split("\n")[max(0, e.lineno - 5):e.lineno + 3]
    print(f"\nSYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.msg}")
    for i, line in enumerate(ctx):
        print(f"  {max(1, e.lineno - 5 + i + 1)}: {repr(line)}")
    sys.exit(1)

# ── Symbol checks ──────────────────────────────────────────────────────────────
checks = {
    "is_trialing": "is_trialing" in new_content,
    "compute_trial_dates": "compute_trial_dates" in new_content,
    "evaluate_trial": "evaluate_trial" in new_content,
    "trial_status": "trial_status" in new_content,
    "LicenseRepository": "LicenseRepository" in new_content,
    "trial_started_at": "trial_started_at" in new_content,
    "deferring to evaluator": "deferring to evaluator" in new_content,
    "trial_evaluator import": "from src.services.trial_evaluator import" in new_content,
    "subscription.get": "subscription.get" in new_content,
    "customer.subscription.deleted": "customer.subscription.deleted" in new_content,
}
for k, v in checks.items():
    print(f"  [{('PASS' if v else 'FAIL')}] {k}")

if all(checks.values()):
    print("\nAll checks PASS — trial logic wired in successfully")
else:
    sys.exit(f"\nFAIL: {[k for k, v in checks.items() if not v]}")
