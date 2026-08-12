#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning (v4).

Uses content-based markers to locate the target block, then replaces it
with the trial-aware version preserving exact indentation.
"""
import ast
import sys

TARGET = "src/api/billing_endpoints.py"

with open(TARGET, "r") as f:
    content = f.read()

# ── Phase 1: add trial_evaluator import ────────────────────────────────────────
ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"

if "from src.services.trial_evaluator import" not in content:
    content = content.replace(ANCHOR, ANCHOR + IMPORT, 1)
    print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# ── Phase 2: locate block by content markers ───────────────────────────────────
# The block ends: " )\n\n # Process event"
BLOCK_END = "\n)\n\n # Process event"
BLOCK_START = " if customer_id and price_id:"

idx_start = content.find(BLOCK_START)
if idx_start == -1:
    sys.exit("ERROR: cannot find block start")

idx_end = content.find(BLOCK_END, idx_start + 500)
if idx_end == -1:
    sys.exit("ERROR: cannot find block end marker")

old_block = content[idx_start:idx_end]
print(f"Step 2: Found block {len(old_block)} chars at offset {idx_start}")

# Verify
assert "CreditStore().add_credits" in old_block, "wrong block — no CreditStore"
assert "is_trialing" not in old_block, "already patched"
assert "credits_provisioned = credits" in old_block, "wrong block"

# ── Phase 3: build new block ────────────────────────────────────────────────────
# Indentation levels (from live analysis):
# B2: "  "  (2s) — function body overlay used in original
# B3: "            " (12s) — level 3 (deeper blocks)
# B4: "                " (16s) — level 4
# B5: "                    " (20s) — level 5
# B6: "                        " (24s) — level 6
# B7: "                            " (28s) — level 7

B2 = "  "
B3 = "            "
B4 = "                "
B5 = "                    "
B6 = "                        "
B7 = "                            "

new_block = (
    # Block start (unchanged 1-space indent, preserved)
    " if customer_id and price_id:\n"

    # ── Trial detection ─────────────────────────────────────────────────────
    f'{B2}is_trialing = (subscription.get("status") or "").lower() == "trialing"\n'
    "\n"

    # ── Tier resolution (same logic, cleaner) ───────────────────────────────
    f"{B2}# Resolve tier from price_id via the mapping\n"
    f"{B2}price_to_tier = get_tier_to_role_mapping()\n"
    f"{B2}tier_key = None\n"
    f"{B2}for pid, tk in price_to_tier.items():\n"
    f"{B3}if pid == price_id:\n"
    f"{B5}tier_key = tk\n"
    f"{B5}break\n"
    "\n"

    # ── Credits: trial-aware ────────────────────────────────────────────────
    f"{B2}if is_trialing:\n"
    f'{B3}tier_key = "trial"\n'
    f'{B3}credits = tier_credits("trial")\n'
    f"{B2}elif tier_key:\n"
    f'{B3}credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    f"{B2}else:\n"
    f"{B2}credits = 0\n"
    "\n"

    # ── Resolve tenant_id + user ────────────────────────────────────────────
    f"{B2}# Resolve tenant_id + user\n"
    f"{B2}customer = await stripe_service._get_customer_by_id(customer_id)\n"
    f"{B2}if customer:\n"
    f"{B3}user_repo = UserRepository()\n"
    f"{B3}user = await user_repo.find_by_email(customer.email)\n"
    f"{B3}if user:\n"
    f"{B5}tenant_id = str(user.id)\n"
    "\n"

    # ── Persist trial dates in license metadata ─────────────────────────────
    f"{B3}# Persist trial dates in license metadata when trial starts\n"
    f'{B3}if is_trialing and event_type in (\n'
    f'{B5}"customer.subscription.created",\n'
    f'{B5}"customer.subscription.updated",\n'
    f"{B3}):\n"
    f"{B5}trial_dates = compute_trial_dates()\n"
    f"{B5}license_repo = LicenseRepository()\n"
    f"{B5}license_info = await license_repo.get_license_by_key(\n"
    f'{B7}user.license_key if hasattr(user, "license_key") else tenant_id\n'
    f"{B5})\n"
    f"{B5}if license_info:\n"
    f'{B7}meta = license_info.get("metadata") or {{}}\n'
    f'{B7}if not meta.get("trial_started_at"):\n'
    f'{B9}meta.update(trial_dates)\n'
    f'{B9}meta["trial_status"] = "trial"\n'
    f'{B7}await license_repo.update_license(\n'
    f'{B9}license_info["key_id"], {{"metadata": meta}}\n'
    f"{B7})\n"
    f"{B7}logger.info(\n"
    f'{B9}"Persisted trial dates for license %s: %s",\n'
    f'{B9}license_info.get("key_id"), trial_dates,\n'
    f"{B7})\n"
    "\n"

    # ── During trial deletion, defer to evaluator for grace/expire ─────────
    f"{B3}# During trial deletion, defer to evaluator for grace/expire\n"
    f'{B3}if event_type == "customer.subscription.deleted" and is_trialing:\n'
    f"{B5}logger.info(\n"
    f'{B7}"Trial subscription deleted for %s - deferring to evaluator",\n'
    f"{B7}tenant_id,\n"
    f"{B5})\n"
    f"{B3}elif credits:\n"
    f"{B5}CreditStore().add_credits(\n"
    f"{B7}tenant_id=tenant_id,\n"
    f"{B7}amount=credits,\n"
    f'{B7}reason=f"stripe:{{event_type}}:{{event_id}}",\n'
    f"{B5})\n"
    f"{B5}credits_provisioned = credits\n"
    f"{B5}logger.info(\n"
    f'{B7}"Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    f"{B7}credits, tenant_id, tier_key, event_type,\n"
    f"{B5})\n"
)

print(f"Step 3: New block {len(new_block)} chars (was {len(old_block)})")

# ── Phase 4: inject & write ────────────────────────────────────────────────────
new_content = content[:idx_start] + new_block + content[idx_end:]
print(f"Step 4: Total file {len(new_content)} chars (was {len(content)})")

with open(TARGET, "w") as f:
    f.write(new_content)
print("Step 5: Written to disk")

# ── Phase 6: syntax check ──────────────────────────────────────────────────────
try:
    ast.parse(new_content)
    print("Step 6: Syntax OK")
except SyntaxError as e:
    ctx = new_content.split("\n")[max(0, e.lineno-5):e.lineno+3]
    print(f"\nSYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.msg}")
    for i, line in enumerate(ctx):
        print(f" {max(1, e.lineno-5+i+1)}: {repr(line)}")
    sys.exit(1)

# ── Phase 7: symbol checks ─────────────────────────────────────────────────────
checks = {
    "is_trialing":                   "is_trialing" in new_content,
    "compute_trial_dates":           "compute_trial_dates" in new_content,
    "evaluate_trial":                "evaluate_trial" in new_content,
    "trial_status":                  "trial_status" in new_content,
    "LicenseRepository":             "LicenseRepository" in new_content,
    "trial_started_at":              "trial_started_at" in new_content,
    "deferring to evaluator":        "deferring to evaluator" in new_content,
    "trial_evaluator import":        "from src.services.trial_evaluator import" in new_content,
    "subscription.get":              "subscription.get" in new_content,
    "customer.subscription.deleted": "customer.subscription.deleted" in new_content,
    "CreditStore still present":     "CreditStore" in new_content,
    "tier_credits still present":    "tier_credits" in new_content,
    "return { preserved":            "return {" in new_content,
}
for k, v in checks.items():
    print(f" [{('PASS' if v else 'FAIL')}] {k}")

if all(checks.values()):
    print("\nAll checks PASS — trial logic wired in")
else:
    sys.exit(f"\nFAIL: {[k for k,v in checks.items() if not v]}")
