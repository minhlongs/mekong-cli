#!/usr/bin/env python3
"""Simple trial patch: find the original block bytes from file, replace with new block."""
import sys

TARGET = "src/api/billing_endpoints.py"

with open(TARGET, "rb") as f:
    raw = f.read()

errors = []

# Step 1: Add import if needed
text = raw.decode("utf-8")
IMPORT_ANCHOR = "from src.raas.credits import CreditStore\n"
IMPORT_LINE = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"

if IMPORT_LINE not in text:
    text = text.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_LINE, 1)
    raw = text.encode("utf-8")
    print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# Step 2: Extract original block from file, build new block, replace
# The original block starts with " if customer_id and price_id:"
# and ends just before "    # Process event" (the next sibling block)
BLOCK_START_MARKER = b" if customer_id and price_id:"
BLOCK_END_MARKER = b"\n\n    # Process event"

idx_start = raw.find(BLOCK_START_MARKER)
if idx_start == -1:
    sys.exit("ERROR: cannot find block start")

idx_end = raw.find(BLOCK_END_MARKER, idx_start + 50)
if idx_end == -1:
    sys.exit("ERROR: cannot find block end marker")

old_block = raw[idx_start:idx_end]
print(f"Step 2: Found block: {len(old_block)} bytes at offset {idx_start}")

# Build new block from the old one, but with trial logic injected
old_text = old_block.decode("utf-8")

# Verify it's the right block
if "CreditStore().add_credits" not in old_text:
    sys.exit("ERROR: found block doesn't contain CreditStore — wrong block?")
if "is_trialing" in old_text:
    sys.exit("ERROR: block already patched")

new_text = old_text

# Insert is_trialing detection right after the block start line
new_text = new_text.replace(
    "if customer_id and price_id:\n",
    'if customer_id and price_id:\n'
    'is_trialing = (subscription.get("status") or "").lower() == "trialing"\n\n',
    1
)

# Replace tier resolution (remove comment, simplify)
new_text = new_text.replace(
    "# Resolve tier from price_id via the mapping\n"
    "price_to_tier = get_tier_to_role_mapping()\n"
    "# Invert: price_id \xe2\x86\x92 tier_key\n"
    "tier_key = None\n"
    "for pid, tk in price_to_tier.items():\n"
    "    if pid == price_id:\n"
    "        tier_key = tk\n"
    "        break\n",
    "# Resolve tier from price_id via the mapping\n"
    "price_to_tier = get_tier_to_role_mapping()\n"
    "tier_key = None\n"
    "for pid, tk in price_to_tier.items():\n"
    "    if pid == price_id:\n"
    "        tier_key = tk\n"
    "        break\n"
)

# Replace credits logic with trial-aware version
new_text = new_text.replace(
    'if tier_key:\n'
    '    credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n',
    'if is_trialing:\n'
    '    tier_key = "trial"\n'
    '    credits = tier_credits("trial")\n'
    'elif tier_key:\n'
    '    credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
    'else:\n'
    '    credits = 0\n'
)

# Update comment
new_text = new_text.replace(
    "# Resolve tenant_id: find user by customer email\n",
    "# Resolve tenant_id + user\n"
)

# Replace the CreditStore block with trial-aware version
old_provision = (
    'CreditStore().add_credits(\n'
    '    tenant_id=tenant_id,\n'
    '    amount=credits,\n'
    '    reason=f"stripe:{event_type}:{event_id}",\n'
    ')\n'
    'credits_provisioned = credits\n'
    'logger.info(\n'
    '    "Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    '    credits, tenant_id, tier_key, event_type,\n'
    ')\n'
)

new_provision = (
    '# Persist trial dates in license metadata when trial starts\n'
    'if is_trialing and event_type in (\n'
    '    "customer.subscription.created",\n'
    '    "customer.subscription.updated",\n'
    '):\n'
    '    trial_dates = compute_trial_dates()\n'
    '    license_repo = LicenseRepository()\n'
    '    license_info = await license_repo.get_license_by_key(\n'
    '        user.license_key if hasattr(user, "license_key") else tenant_id\n'
    '    )\n'
    '    if license_info:\n'
    '        meta = license_info.get("metadata") or {}\n'
    '        if not meta.get("trial_started_at"):\n'
    '            meta.update(trial_dates)\n'
    '            meta["trial_status"] = "trial"\n'
    '        await license_repo.update_license(\n'
    '            license_info["key_id"], {"metadata": meta}\n'
    '        )\n'
    '        logger.info(\n'
    '            "Persisted trial dates for license %s: %s",\n'
    '            license_info.get("key_id"), trial_dates,\n'
    '        )\n'
    '\n'
    '# During trial deletion, defer to evaluator for grace/expire\n'
    'if event_type == "customer.subscription.deleted" and is_trialing:\n'
    '    logger.info(\n'
    '        "Trial subscription deleted for %s - deferring to evaluator",\n'
    '        tenant_id,\n'
    '    )\n'
    'elif credits:\n'
    '    CreditStore().add_credits(\n'
    '        tenant_id=tenant_id,\n'
    '        amount=credits,\n'
    '        reason=f"stripe:{event_type}:{event_id}",\n'
    '    )\n'
    '    credits_provisioned = credits\n'
    '    logger.info(\n'
    '        "Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
    '        credits, tenant_id, tier_key, event_type,\n'
    '    )\n'
)

if old_provision not in new_text:
    sys.exit("ERROR: cannot find old provision block in text")
new_text = new_text.replace(old_provision, new_provision, 1)

# Assemble
new_raw = raw[:idx_start] + new_text.encode("utf-8") + raw[idx_end:]

with open(TARGET, "wb") as f:
    f.write(new_raw)
print(f"Written: {len(new_raw)} bytes")

# Verify syntax
import ast  # noqa: E402
try:
    ast.parse(new_raw.decode("utf-8"))
    print("Syntax: OK")
except SyntaxError as e:
    ctx = new_raw.decode("utf-8").split("\n")[max(0, e.lineno - 5):e.lineno + 3]
    print(f"\nSYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.msg}")
    for i, line in enumerate(ctx):
        print(f"  {max(1,e.lineno-5+i)+1}: {repr(line)}")
    sys.exit(1)

# Symbol checks
full = new_raw.decode("utf-8")
checks = {
    "is_trialing":             "is_trialing" in full,
    "compute_trial_dates":     "compute_trial_dates" in full,
    "evaluate_trial":          "evaluate_trial" in full,
    "trial_status":            "trial_status" in full,
    "LicenseRepository":       "LicenseRepository" in full,
    "trial_started_at":        "trial_started_at" in full,
    "deferring to evaluator":  "deferring to evaluator" in full,
    "trial_evaluator import":  "from src.services.trial_evaluator import" in full,
}
for k, v in checks.items():
    print(f"  [{('PASS' if v else 'FAIL')}] {k}")

if all(checks.values()):
    print("\nAll checks PASS")
else:
    print(f"\nFAIL: {[k for k,v in checks.items() if not v]}")
    sys.exit(1)
