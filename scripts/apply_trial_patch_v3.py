#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning.

Byte-offset approach: replace bytes 24590:25985 (old block inclusive of 'return {')
with the new trial-aware version. Indent verified from live file analysis.
"""
import ast
import sys

TARGET = "src/api/billing_endpoints.py"

with open(TARGET, "rb") as f:
    raw = f.read()

# Verified byte offsets from byte-level analysis
B0, B1 = 24590, 25942
old = raw[B0:B1]
assert old.startswith(b' if customer_id and price_id:'), "Block start mismatch"
assert b'CreditStore' in old, "Block doesn't contain CreditStore"
assert b'is_trialing' not in old, "Block already patched"

# Indent constants (4-space per level, confirmed from file)
I  = b' ' * 12  # body (level 3)
INDENT4 = b' ' * 16  # inner if/for (level 4)
INDENT5 = b' ' * 20  # innermost (level 5)
INDENT6 = b' ' * 24  # tenant_id/CreditStore assign level (level 6)
INDENT7 = b' ' * 28  # CreditStore kwargs + logger args (level 7)

new = [
I,  b'is_trialing = (subscription.get("status") or "").lower() == "trialing"\n',
I,  b'\n',
I,  b'# Resolve tier from price_id via the mapping\n',
I,  b'price_to_tier = get_tier_to_role_mapping()\n',
I,  b'tier_key = None\n',
I,  b'for pid, tk in price_to_tier.items():\n',
INDENT6, b'if pid == price_id:\n',
INDENT7, b'tier_key = tk\n',
INDENT7, b'break\n',
I,  b'\n',
I,  b'if is_trialing:\n',
INDENT6, b'tier_key = "trial"\n',
INDENT6, b'credits = tier_credits("trial")\n',
I,  b'elif tier_key:\n',
INDENT6, b'credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n',
I,  b'else:\n',
INDENT6, b'credits = 0\n',
I,  b'\n',
I,  b'# Resolve tenant_id + user\n',
I,  b'customer = await stripe_service._get_customer_by_id(customer_id)\n',
I,  b'if customer:\n',
INDENT6, b'user_repo = UserRepository()\n',
INDENT6, b'user = await user_repo.find_by_email(customer.email)\n',
INDENT6, b'if user:\n',
INDENT7, b'tenant_id = str(user.id)\n',
INDENT7, b'\n',
INDENT7, b'# Persist trial dates in license metadata when trial starts\n',
INDENT6, b'if is_trialing and event_type in (\n',
INDENT7, b'"customer.subscription.created",\n',
INDENT7, b'"customer.subscription.updated",\n',
INDENT6, b'):\n',
INDENT7, b'trial_dates = compute_trial_dates()\n',
INDENT7, b'license_repo = LicenseRepository()\n',
INDENT7, b'license_info = await license_repo.get_license_by_key(\n',
INDENT6, b'user.license_key if hasattr(user, "license_key") else tenant_id\n',
INDENT7, b')\n',
INDENT7, b'if license_info:\n',
INDENT6, b'meta = license_info.get("metadata") or {}\n',
INDENT6, b'if not meta.get("trial_started_at"):\n',
INDENT7, b'meta.update(trial_dates)\n',
INDENT7, b'meta["trial_status"] = "trial"\n',
INDENT6, b'await license_repo.update_license(\n',
INDENT7, b'license_info["key_id"], {"metadata": meta}\n',
INDENT6, b')\n',
INDENT6, b'logger.info(\n',
INDENT7, b'"Persisted trial dates for license %s: %s",\n',
INDENT7, b'license_info.get("key_id"), trial_dates,\n',
INDENT6, b')\n',
INDENT7, b'\n',
INDENT7, b'# During trial deletion, defer to evaluator for grace/expire\n',
INDENT6, b'if event_type == "customer.subscription.deleted" and is_trialing:\n',
INDENT7, b'logger.info(\n',
INDENT6, b'"Trial subscription deleted for %s - deferring to evaluator",\n',
INDENT6, b'tenant_id,\n',
INDENT7, b')\n',
INDENT6, b'elif credits:\n',
INDENT7, b'CreditStore().add_credits(\n',
INDENT6, b'tenant_id=tenant_id,\n',
INDENT6, b'amount=credits,\n',
INDENT6, b'reason=f"stripe:{event_type}:{event_id}",\n',
INDENT7, b')\n',
INDENT7, b'credits_provisioned = credits\n',
INDENT7, b'logger.info(\n',
INDENT6, b'"Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n',
INDENT6, b'credits, tenant_id, tier_key, event_type,\n',
INDENT7, b')\n',
]

new_block = b''.join(new)
assert b'return {' not in new_block, "return { leaked into body!"

# Step 1: add import
content = raw.decode("utf-8")
anchor = "from src.raas.credits import CreditStore\n"
imp = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"
if imp not in content:
    content = content.replace(anchor, anchor + imp, 1)
    print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# Step 2: inject new block, preserve 'return {' after block
raw2 = content.encode("utf-8")
old_injected = raw2[B0:B1]
assert b'is_trialing' not in old_injected, "Already patched in injected copy"
new_raw = raw2[:B0] + new_block + raw2[B1:]
print(f"Step 2: Injected {len(new_block)} bytes (was {len(old_injected)})")

# Step 3: write
with open(TARGET, "wb") as f:
    f.write(new_raw)
print("Step 3: Written to disk")

# Step 4: syntax check
try:
    ast.parse(new_raw.decode("utf-8"))
    print("Step 4: Syntax OK")
except SyntaxError as e:
    ctx = new_raw.decode().split("\n")[max(0, e.lineno-5):e.lineno+3]
    print(f"\nSYNTAX ERROR line {e.lineno}, col {e.offset}: {e.msg}")
    for i, line in enumerate(ctx):
        print(f"  {max(1,e.lineno-5+i+1)}: {repr(line)}")
    sys.exit(1)

# Step 5: symbol checks
full = new_raw.decode("utf-8")
checks = {
    "is_trialing": "is_trialing" in full,
    "compute_trial_dates": "compute_trial_dates" in full,
    "evaluate_trial": "evaluate_trial" in full,
    "trial_status": "trial_status" in full,
    "LicenseRepository": "LicenseRepository" in full,
    "trial_started_at": "trial_started_at" in full,
    "deferring to evaluator": "deferring to evaluator" in full,
    "trial_evaluator import": "from src.services.trial_evaluator import" in full,
    "CreditStore still present": "CreditStore" in full,
    "tier_credits still present": "tier_credits" in full,
}
for k, v in checks.items():
    print(f"  [{'PASS' if v else 'FAIL'}] {k}")

if all(checks.values()):
    print("\nAll checks PASS — trial logic wired in")
else:
    sys.exit(f"\nFAIL: {[k for k,v in checks.items() if not v]}")
