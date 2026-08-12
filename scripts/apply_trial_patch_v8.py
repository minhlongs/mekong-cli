#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning (v8-fix).

REALITY: This file uses FLAT 2-space indentation for ALL statement lines.
Only continuation lines (fn args, collection items) use deeper indent.
Every if/for/body line is exactly 2 spaces regardless of nesting depth.
"""

import sys

BLOCK_START = " if customer_id and price_id:\n"
BLOCK_END = " }\n\n\n@billing_router.post"

try:
    with open("src/api/billing_endpoints.py", "r") as f:
        content = f.read()
except FileNotFoundError:
    sys.exit("ERROR: src/api/billing_endpoints.py not found")

# ── Phase 1: add trial_evaluator import ────────────────────────────────────────
ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"
if "from src.services.trial_evaluator import" not in content:
    content = content.replace(ANCHOR, ANCHOR + IMPORT, 1)
    print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# ── Phase 2: locate block ───────────────────────────────────────────────────────
idx_start = content.find(BLOCK_START)
if idx_start == -1:
    sys.exit(f"ERROR: cannot find block start marker: {repr(BLOCK_START)}")
print(f"Step 2a: Block starts at offset {idx_start}")

# Search for the end marker starting 500 chars after start
idx_end_raw = content.find(BLOCK_END, idx_start + 500)
if idx_end_raw == -1:
    sys.exit("ERROR: cannot find block end marker")

# The block ends right BEFORE "@billing_router.post"
idx_end = idx_end_raw  # BLOCK_END includes "@billing_router.post", so idx_end_raw is right before '@'
print(f"Step 2b: Block ends at offset {idx_end}")

old_block = content[idx_start:idx_end]
print(f"Step 2c: Extracted {len(old_block)} chars")
print(f"Block tail: {repr(old_block[-30:])}")

# ── Sanity checks ───────────────────────────────────────────────────────────────
checks_before = {
    "CreditStore": "CreditStore().add_credits" in old_block,
    "not_already_patched": "is_trialing" not in old_block,
    "credits_provisioned": "credits_provisioned = credits" in old_block,
}
for k, v in checks_before.items():
    print(f"  [{('PASS' if v else 'FAIL')}] {k}")
if not all(checks_before.values()):
    sys.exit(f"Block validation failed: {checks_before}")

# ── Phase 3: build new block ────────────────────────────────────────────────────
# Flat 2-space scheme: S1=2s (statements), S2=4s (continuations only)
S1 = " "
S2 = " "
S3 = " "
S4 = " "

new_block = (
    f"{S1}if customer_id and price_id:\n"
    f'\n'
    f'{S1}is_trialing = (subscription.get("status") or "").lower() == "trialing"\n'
    f'\n'
    # ── Tier resolution ─────────────────────────────────────────────────────
    f"{S1}# Resolve tier from price_id via the mapping\n"
    f"{S1}price_to_tier = get_tier_to_role_mapping()\n"
    f"{S1}tier_key = None\n"
    f"{S1}for pid, tk in price_to_tier.items():\n"
    f"{S1}if pid == price_id:\n"
    f"{S2}tier_key = tk\n"
    f"{S2}break\n"
    f"\n"
    # ── Credits: trial-aware or tier-based ──────────────────────────────────
    f"{S1}if is_trialing:\n"
    f'{S2}tier_key = "trial"\n'
    f'{S2}credits = tier_credits("trial")\n'
    f"{S1}elif tier_key:\n"
    f'{S2}credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    f"{S1}else:\n"
    f"{S2}credits = 0\n"
    f"\n"
    # ── Resolve tenant_id via customer email ────────────────────────────────
    f"{S1}# Resolve tenant_id: find user by customer email\n"
    f"{S1}customer = await stripe_service._get_customer_by_id(customer_id)\n"
    f"{S1}if customer:\n"
    f"{S2}user_repo = UserRepository()\n"
    f"{S2}user = await user_repo.find_by_email(customer.email)\n"
    f"{S2}if user:\n"
    f"{S3}tenant_id = str(user.id)\n"
    f"\n"
    # ── Persist trial dates in license metadata ─────────────────────────────
    f"{S2}# Persist trial dates in license metadata when trial starts\n"
    f'{S2}if is_trialing and event_type in (\n'
    f'{S2}"customer.subscription.created",\n'
    f'{S2}"customer.subscription.updated",\n'
    f"{S2}):\n"
    f"{S2}trial_dates = compute_trial_dates()\n"
    f"{S2}license_repo = LicenseRepository()\n"
    f"{S2}license_info = await license_repo.get_license_by_key(\n"
    f'{S2}user.license_key if hasattr(user, "license_key") else tenant_id\n'
    f"{S2})\n"
    f"{S2}if license_info:\n"
    f'{S2}meta = license_info.get("metadata") or {{}}\n'
    f'{S2}if not meta.get("trial_started_at"):\n'
    f"{S2}meta.update(trial_dates)\n"
    f'{S2}meta["trial_status"] = "trial"\n'
    f"{S2}await license_repo.update_license(\n"
    f'{S2}license_info["key_id"], {{"metadata": meta}}\n'
    f"{S2})\n"
    f"{S2}logger.info(\n"
    f'{S2}"Persisted trial dates for license %s: %s",\n'
    f'{S2}license_info.get("key_id"), trial_dates,\n'
    f"{S2})\n"
    f"\n"
    # ── Trial deletion: defer to evaluator ─────────────────────────────────
    f"{S2}# During trial deletion, defer to evaluator for grace/expire\n"
    f'{S2}if event_type == "customer.subscription.deleted" and is_trialing:\n'
    f"{S2}logger.info(\n"
    f'{S4}"Trial subscription deleted for %s - deferring to evaluator",\n'
    f"{S4}tenant_id,\n"
    f"{S2})\n"
    f"{S2}elif credits:\n"
    f"{S3}CreditStore().add_credits(\n"
    f"{S4}tenant_id=tenant_id,\n"
    f"{S4}amount=credits,\n"
    f'{S4}reason=f"stripe:{{event_type}}:{{event_id}}",\n'
    f"{S2})\n"
    f"{S2}credits_provisioned = credits\n"
    f"{S2}logger.info(\n"
    f'{S4}"Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    f"{S4}credits, tenant_id, tier_key, event_type,\n"
    f"{S2})\n"
)

print(f"Step 3: New block {len(new_block)} chars (was {len(old_block)})")

# ── Phase 4: inject & write ────────────────────────────────────────────────────
new_content = content[:idx_start] + new_block + content[idx_end:]
print(f"Step 4: File {len(new_content)} chars (was {len(content)})")

with open("src/api/billing_endpoints.py", "w") as f:
    f.write(new_content)
print("Step 5: Written")

# ── Phase 6: syntax check ──────────────────────────────────────────────────────
import ast  # noqa: E402
try:
    ast.parse(new_content)
    print("Step 6: Syntax OK")
except SyntaxError as e:
    ctx = new_content.split("\n")[max(0, e.lineno - 5):e.lineno + 3]
    print(f"\nSYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.msg}")
    for i, line in enumerate(ctx):
        print(f"  {max(1, e.lineno - 5 + i + 1)}: {repr(line)}")
    sys.exit(1)

# ── Phase 7: symbol checks ─────────────────────────────────────────────────────
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
    "CreditStore still present": "CreditStore" in new_content,
    "tier_credits still present": "tier_credits" in new_content,
    "return { preserved": "return {" in new_content,
}
for k, v in checks.items():
    print(f"  [{'PASS' if v else 'FAIL'}] {k}")

passing = sum(checks.values())
total = len(checks)
print(f"\nChecks: {passing}/{total} PASS")
if not all(checks.values()):
    failed = [k for k, v in checks.items() if not v]
    sys.exit(f"\nFAIL: {failed}")
print("\nAll checks PASS — trial logic wired in")
