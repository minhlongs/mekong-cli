"""Wire trial system into the credit-provisioning block in billing_endpoints.py.

Extracts the exact flat-block from the file byte-for-byte, then replaces it.
Handles Step 1 (imports) + Step 2 (block replacement) in one pass.
"""
import ast

with open("src/api/billing_endpoints.py", "rb") as f:
    raw = f.read()

errors = []

# ── Step 1: Add trial_evaluator import if missing ─────────────────────────────
content_str = raw.decode("utf-8")

if "compute_trial_dates" not in content_str:
    content_str = content_str.replace(
        "from src.raas.credits import CreditStore\n",
        "from src.raas.credits import CreditStore\n"
        "from src.services.trial_evaluator import compute_trial_dates, evaluate_trial\n",
        1,
    )
    print("Step 1: Added trial_evaluator import")
else:
    print("Step 1: Import already present")

# ── Step 2: Replace the flat block ─────────────────────────────────────────────
# Verify the block start marker
marker = "if customer_id and price_id: # Resolve tier from price_id via the mapping"
idx = content_str.find(marker)
if idx == -1:
    errors.append("Cannot find block start marker")
else:
    # Find the block end: three newlines followed by 'return {'
    end_search_start = idx + 100
    end_marker = "\n\n\nreturn {\n \"status\""
    end_idx = content_str.find(end_marker, end_search_start)
    if end_idx == -1:
        errors.append("Cannot find block end marker (triple newline + return)")
    else:
        old_block = content_str[idx:end_idx + 1]  # include the \n before return
        new_block = old_block  # will be rewritten below

        # Build the replacement by reading from the file directly
        # and substituting the internal logic
        # The block is flat — Python parses inner statements as part of
        # the parent `if event_type in (...):` block.

        # Extract the preserved parts (before and after the tier_credits line)
        tier_line_start = old_block.find("credits = tier_credits(tier_key)")
        tier_line_end = old_block.find("else 0\n", tier_line_start) + len("else 0")

        before_tier = old_block[:tier_line_start]
        after_tier = old_block[tier_line_end:]

        new_block = (
            before_tier
            + "is_trialing = (subscription.get(\"status\") or \"\").lower() == \"trialing\"\n\n"
            " price_to_tier = get_tier_to_role_mapping()\n"
            " # Invert: price_id -> tier_key\n"
            " tier_key = None\n"
            " for pid, tk in price_to_tier.items():\n"
            " if pid == price_id:\n"
            " tier_key = tk\n"
            " break\n\n"
            " if is_trialing:\n"
            " tier_key = \"trial\"\n"
            " credits = tier_credits(\"trial\")\n"
            + after_tier.replace(
                "# Resolve tenant_id: find user by customer email\n",
                "# Resolve tenant_id + user\n"
            ).replace(
                "CreditStore().add_credits(\n tenant_id=tenant_id,\n amount=credits,\n reason=f\"stripe:{event_type}:{event_id}\",\n )\n credits_provisioned = credits\n logger.info(\n \"Provisioned %d credits for tenant %s (tier=%s, event=%s)\",\n credits, tenant_id, tier_key, event_type,\n )\n",
                "# Persist trial dates in license metadata when trial starts\n"
                " if is_trialing and event_type in (\n"
                " \"customer.subscription.created\",\n"
                " \"customer.subscription.updated\",\n"
                " ):\n"
                " trial_dates = compute_trial_dates()\n"
                " license_repo = LicenseRepository()\n"
                " license_info = await license_repo.get_license_by_key(\n"
                " user.license_key if hasattr(user, \"license_key\") else tenant_id\n"
                " )\n"
                " if license_info:\n"
                " meta = license_info.get(\"metadata\") or {}\n"
                " if not meta.get(\"trial_started_at\"):\n"
                " meta.update(trial_dates)\n"
                " meta[\"trial_status\"] = \"trial\"\n"
                " await license_repo.update_license(\n"
                " license_info[\"key_id\"], {\"metadata\": meta}\n"
                " )\n"
                " logger.info(\n"
                ' "Persisted trial dates for license %s: %s",\n'
                " license_info.get(\"key_id\"), trial_dates,\n"
                " )\n\n"
                "# During trial deletion, defer to evaluator for grace/expire\n"
                " if event_type == \"customer.subscription.deleted\" and is_trialing:\n"
                " logger.info(\n"
                ' "Trial subscription deleted for %s - deferring to evaluator",\n'
                " tenant_id,\n"
                " )\n"
                " elif credits:\n"
                " CreditStore().add_credits(\n"
                " tenant_id=tenant_id,\n"
                " amount=credits,\n"
                ' reason=f"stripe:{event_type}:{event_id}",\n'
                " )\n"
                " credits_provisioned = credits\n"
                " logger.info(\n"
                ' "Provisioned %d credits for tenant %s (tier=%s, event=%s)",\n'
                " credits, tenant_id, tier_key, event_type,\n"
                " )\n"
            ).rstrip("\n") + "\n"
        )

        content_str = content_str[:idx] + new_block + content_str[end_idx + 1:]
        print("Step 2: Block replaced with trial-aware logic")

# ── Write + verify ─────────────────────────────────────────────────────────────
if errors:
    print("ERRORS:")
    for e in errors:
        print(f" - {e}")
else:
    with open("src/api/billing_endpoints.py", "w") as f:
        f.write(content_str)
    print("Written — verifying syntax...")
    try:
        ast.parse(content_str)
        print("Syntax: OK")
    except SyntaxError as e:
        print(f"SYNTAX ERROR at line {e.lineno}, col {e.offset}")
        print(f"  {e.text}")
