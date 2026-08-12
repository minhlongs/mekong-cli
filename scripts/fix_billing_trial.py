"""Step 2a: Add trial_evaluator import if missing in src/api/billing_endpoints.py
Step 2b: Replace credit-provisioning block with trial-aware logic.

Uses anchored regex from the block start to find block end reliably.
Assembles final content = new_imports + old_before_import + modified_block + rest.
"""
import ast
import re
import sys

with open("src/api/billing_endpoints.py", "r") as f:
    content = f.read()

S = " "  # 1-space flat indent

# ── Step 2a: Add trial_evaluator import at top if missing ─────────────────────
IMPORT_ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT_LINE  = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"

if "from src.services.trial_evaluator import" not in content:
    content = content.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_LINE, 1)
    print("Step 2a: Added trial_evaluator import")
else:
    print("Step 2a: Import already present")

# ── Step 2b: Locate and replace the flat-indent block ─────────────────────────
pattern = re.compile(r' if customer_id and price_id:.*?return \{', re.DOTALL)
m = pattern.search(content)
if not m:
    sys.exit("ERROR: regex did not match the block end")
i_start = m.start()
i_end   = m.end()  # include 'return {'
old_block = content[i_start:i_end]
if "is_trialing" in old_block:
    sys.exit("Block already has trial logic — aborting")

print(f"Step 2b: Found block bytes {i_start}-{i_end} ({len(old_block)} chars)")

new_block = (
    " if customer_id and price_id:\n"
    " is_trialing = (subscription.get(\"status\") or \"\").lower() == \"trialing\"\n"
    "\n"
    " # Resolve tier from price_id via the mapping\n"
    " price_to_tier = get_tier_to_role_mapping()\n"
    " tier_key = None\n"
    " for pid, tk in price_to_tier.items():\n"
    "  if pid == price_id:\n"
    "   tier_key = tk\n"
    "   break\n"
    "\n"
    " if is_trialing:\n"
    "  tier_key = \"trial\"\n"
    "  credits = tier_credits(\"trial\")\n"
    " elif tier_key:\n"
    "  credits = tier_credits(tier_key) if event_type != \"customer.subscription.deleted\" else 0\n"
    " else:\n"
    "  credits = 0\n"
    "\n"
    " # Resolve tenant_id + user\n"
    " customer = await stripe_service._get_customer_by_id(customer_id)\n"
    " if customer:\n"
    "  user_repo = UserRepository()\n"
    "  user = await user_repo.find_by_email(customer.email)\n"
    "  if user:\n"
    "   tenant_id = str(user.id)\n"
    "\n"
    " # Persist trial dates in license metadata when trial starts\n"
    " if is_trialing and event_type in (\n"
    "  \"customer.subscription.created\",\n"
    "  \"customer.subscription.updated\",\n"
    " ):\n"
    "  trial_dates = compute_trial_dates()\n"
    "  license_repo = LicenseRepository()\n"
    "  license_info = await license_repo.get_license_by_key(\n"
    "   user.license_key if hasattr(user, \"license_key\") else tenant_id\n"
    "  )\n"
    "  if license_info:\n"
    "   meta = license_info.get(\"metadata\") or {}\n"
    "   if not meta.get(\"trial_started_at\"):\n"
    "    meta.update(trial_dates)\n"
    "    meta[\"trial_status\"] = \"trial\"\n"
    "   await license_repo.update_license(\n"
    "    license_info[\"key_id\"], {\"metadata\": meta}\n"
    "   )\n"
    "   logger.info(\n"
    "    \"Persisted trial dates for license %s: %s\",\n"
    "    license_info.get(\"key_id\"), trial_dates,\n"
    "   )\n"
    "\n"
    " # During trial deletion, defer to evaluator for grace/expire\n"
    " if event_type == \"customer.subscription.deleted\" and is_trialing:\n"
    "  logger.info(\n"
    "   \"Trial subscription deleted for %s - deferring to evaluator\",\n"
    "   tenant_id,\n"
    "  )\n"
    " elif credits:\n"
    "  CreditStore().add_credits(\n"
    "   tenant_id=tenant_id,\n"
    "   amount=credits,\n"
    '   reason=f"stripe:{event_type}:{event_id}",\n'
    "  )\n"
    "  credits_provisioned = credits\n"
    "  logger.info(\n"
    '   "Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    "   credits, tenant_id, tier_key, event_type,\n"
    "  )\n"
)

# Inject
new_content = content[:i_start] + new_block + content[i_end:]
print(f"Step 2b: Injected {len(new_block)} chars (was {len(old_block)})")

# Write + verify
with open("src/api/billing_endpoints.py", "w") as f:
    f.write(new_content)
print("Written — verifying syntax...")

try:
    ast.parse(new_content)
    print("Syntax: OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.text}")
    sys.exit(1)

checks = {
    "is_trialing":             "is_trialing" in new_content,
    "compute_trial_dates":     "compute_trial_dates" in new_content,
    "evaluate_trial":          "evaluate_trial" in new_content,
    "trial_status":            'trial_status' in new_content,
    "LicenseRepository":       "LicenseRepository" in new_content,
    "trial_started_at":        "trial_started_at" in new_content,
    "deferring to evaluator":  "deferring to evaluator" in new_content,
    "tier_key=None flow":      "tier_key = None\n" in new_content,
    "trial_evaluator import":  "from src.services.trial_evaluator import" in new_content,
}
for k, v in checks.items():
    print(f"  {k}: {v}")

if all(checks.values()):
    print("\nStep 2: All checks PASS — trial logic wired in")
else:
    sys.exit(f"\nFAIL: {[k for k, v in checks.items() if not v]}")
