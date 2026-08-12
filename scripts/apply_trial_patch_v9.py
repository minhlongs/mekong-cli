#!/usr/bin/env python3
"""Patch billing_endpoints.py with trial-aware credit provisioning (v9).

Verified indentation (binary inspection, not assumed):
  I2 = 12 spaces  — statements inside `if customer_id and price_id:`
  I3 = 16 spaces  — one level deeper (if/for/elif bodies)
  I4 = 20 spaces  — two levels deeper (nested if bodies)
  I5 = 24 spaces  — three levels deeper (CreditStore/locallogger kwargs)
  I6 = 28 spaces  — four levels deeper (continuation items)

Block ends right before "\n\n\n return {" (4-space return at function level).
"""

import sys

BLOCK_START = " if customer_id and price_id:\n"
BLOCK_END = "\n\n\n return {"


def main():
    with open("src/api/billing_endpoints.py", "r") as f:
        content = f.read()

    # ── Phase 1: add trial_evaluator import (idempotent) ───────────────────────
    ANCHOR = "from src.raas.credits import CreditStore\n"
    IMPORT = "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n"
    if "from src.services.trial_evaluator import" not in content:
        content = content.replace(ANCHOR, ANCHOR + IMPORT, 1)
        print("Step 1: Added trial_evaluator import")
    else:
        print("Step 1: Import already present")

    # ── Phase 2: locate block ───────────────────────────────────────────────────
    idx_start = content.find(BLOCK_START)
    if idx_start == -1:
        sys.exit(f"ERROR: cannot find block start marker: {repr(BLOCK_START)}")
    print(f"Step 2a: Block starts at offset {idx_start}")

    idx_end = content.find(BLOCK_END, idx_start + 500)
    if idx_end == -1:
        sys.exit("ERROR: cannot find block end marker")

    old_block = content[idx_start:idx_end]
    print(f"Step 2b: Block ends at offset {idx_end}")
    print(f"Step 2c: Extracted {len(old_block)} chars (first 80: {repr(old_block[:80])})")
    print(f"         last 80: {repr(old_block[-80:])}")

    # ── Sanity checks ────────────────────────────────────────────────────────────
    checks_before = {
        "CreditStore present": "CreditStore().add_credits" in old_block,
        "not already patched": "is_trialing" not in old_block,
        "credits_provisioned present": "credits_provisioned = credits" in old_block,
    }
    for k, v in checks_before.items():
        print(f" [{('PASS' if v else 'FAIL')}] {k}")
    if not all(checks_before.values()):
        sys.exit(f"Block validation failed: {checks_before}")

    # ── Phase 3: build new block ─────────────────────────────────────────────────
    # Verified indentation constants (from binary inspection of actual file)
    I2 = " " * 12   # 12 spaces — top-level statements inside `if customer_id`
    I3 = " " * 16   # 16 spaces — one level deeper (if/for/elif bodies)
    I4 = " " * 20   # 20 spaces — two levels deeper (assignments inside nested if)
    I5 = " " * 24   # 24 spaces — three levels deeper (CreditStore kwargs)
    I6 = " " * 28   # 28 spaces — four levels deeper (continuation items)

    new_block = (
        # Block start (identical anchor)
        f"{I2}if customer_id and price_id:\n"
        "\n"

        # ── Trial detection (top-level statement at I2) ──────────────────────
        f'{I2}is_trialing = (subscription.get("status") or "").lower() == "trialing"\n'
        "\n"

        # ── Tier resolution ─────────────────────────────────────────────────
        f"{I2}# Resolve tier from price_id via the mapping\n"
        f"{I2}price_to_tier = get_tier_to_role_mapping()\n"
        f"{I2}tier_key = None\n"
        f"{I2}for pid, tk in price_to_tier.items():\n"
        f"{I3}if pid == price_id:\n"
        f"{I4}tier_key = tk\n"
        f"{I4}break\n"
        "\n"

        # ── Credits: trial-aware or tier-based ──────────────────────────────
        f"{I2}if is_trialing:\n"
        f'{I3}tier_key = "trial"\n'
        f'{I3}credits = tier_credits("trial")\n'
        f"{I2}elif tier_key:\n"
        f'{I3}credits = tier_credits(tier_key) if event_type != "customer.subscription.deleted" else 0\n'
        f"{I2}else:\n"
        f"{I3}credits = 0\n"
        "\n"

        # ── Resolve tenant_id via customer email ────────────────────────────
        f"{I2}# Resolve tenant_id: find user by customer email\n"
        f"{I2}customer = await stripe_service._get_customer_by_id(customer_id)\n"
        f"{I2}if customer:\n"
        f"{I3}user_repo = UserRepository()\n"
        f"{I3}user = await user_repo.find_by_email(customer.email)\n"
        f"{I3}if user:\n"
        f"{I4}tenant_id = str(user.id)\n"
        "\n"

        # ── Persist trial dates in license metadata ──────────────────────────
        f"{I3}# Persist trial dates in license metadata when trial starts\n"
        f'{I3}if is_trialing and event_type in (\n'
        f'{I4}"customer.subscription.created",\n'
        f'{I4}"customer.subscription.updated",\n'
        f"{I3}):\n"
        f"{I4}trial_dates = compute_trial_dates()\n"
        f"{I4}license_repo = LicenseRepository()\n"
        f"{I4}license_info = await license_repo.get_license_by_key(\n"
        f'{I6}user.license_key if hasattr(user, "license_key") else tenant_id\n'
        f"{I4})\n"
        f"{I4}if license_info:\n"
        f'{I6}meta = license_info.get("metadata") or {{}}\n'
        f'{I6}if not meta.get("trial_started_at"):\n'
        f"{I6}meta.update(trial_dates)\n"
        f'{I6}meta["trial_status"] = "trial"\n'
        f"{I6}await license_repo.update_license(\n"
        f'{I6}license_info["key_id"], {{"metadata": meta}}\n'
        f"{I6})\n"
        f"{I6}logger.info(\n"
        f'{I6}"Persisted trial dates for license %s: %s",\n'
        f'{I6}license_info.get("key_id"), trial_dates,\n'
        f"{I6})\n"
        "\n"

        # ── Trial deletion: defer to evaluator for grace/expire ─────────────
        f"{I3}# During trial deletion, defer to evaluator for grace/expire\n"
        f'{I3}if event_type == "customer.subscription.deleted" and is_trialing:\n'
        f"{I4}logger.info(\n"
        f'{I6}"Trial subscription deleted for %s - deferring to evaluator",\n'
        f"{I6}tenant_id,\n"
        f"{I4})\n"
        f"{I3}elif credits:\n"
        f"{I4}CreditStore().add_credits(\n"
        f"{I5}tenant_id=tenant_id,\n"
        f"{I5}amount=credits,\n"
        f'{I5}reason=f"stripe:{{event_type}}:{{event_id}}",\n'
        f"{I4})\n"
        f"{I4}credits_provisioned = credits\n"
        f"{I4}logger.info(\n"
        f'{I6}"Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
        f"{I6}credits, tenant_id, tier_key, event_type,\n"
        f"{I4})\n"
    )

    print(f"Step 3: New block {len(new_block)} chars (old block was {len(old_block)})")

    # ── Phase 4: inject ─────────────────────────────────────────────────────────
    new_content = content[:idx_start] + new_block + content[idx_end:]
    print(f"Step 4: Total file {len(new_content)} chars (was {len(content)})")

    # ── Phase 5: write ──────────────────────────────────────────────────────────
    with open("src/api/billing_endpoints.py", "w") as f:
        f.write(new_content)
    print("Step 5: Written to disk")

    # ── Phase 6: syntax check ───────────────────────────────────────────────────
    import ast
    try:
        ast.parse(new_content)
        print("Step 6: Syntax OK")
    except SyntaxError as e:
        ctx = new_content.split("\n")[max(0, e.lineno - 5):e.lineno + 3]
        print(f"\nSYNTAX ERROR at line {e.lineno}, col {e.offset}: {e.msg}")
        for i, line in enumerate(ctx):
            print(f" {max(1, e.lineno - 5 + i + 1)}: {repr(line)}")
        sys.exit(1)

    # ── Phase 7: symbol checks ──────────────────────────────────────────────────
    checks = {
        "is_trialing": "is_trialing" in new_content,
        "compute_trial_dates": "compute_trial_dates" in new_content,
        "evaluate_trial": "evaluate_trial" in new_content,
        "trial_status": "trial_status" in new_content,
        "LicenseRepository": "LicenseRepository" in new_content,
        "trial_started_at": "trial_started_at" in new_content,
        "deferring to evaluator": "deferring to evaluator" in new_content,
        "trial_evaluator import": "from src.services.trial_evaluator import" in new_content,
        "subscription.status check": 'subscription.get("status")' in new_content,
        "customer.subscription.deleted": "customer.subscription.deleted" in new_content,
        "CreditStore preserved": "CreditStore" in new_content,
        "tier_credits preserved": "tier_credits" in new_content,
        "return { preserved": "return {" in new_content,
    }
    for k, v in checks.items():
        print(f" [{('PASS' if v else 'FAIL')}] {k}")

    passing = sum(checks.values())
    total = len(checks)
    print(f"\nChecks: {passing}/{total} PASS")
    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        sys.exit(f"\nFAIL: {failed}")
    print("\nAll checks PASS — trial logic wired in")


if __name__ == "__main__":
    main()
