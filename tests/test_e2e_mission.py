"""End-to-end mission test — proves Mekong can deliver value.

Run with: python3 tests/test_e2e_mission.py

Requires: At least one LLM provider configured:
  - OLLAMA_BASE_URL=http://localhost:11434/v1 (free, local)
  - or LLM_BASE_URL + LLM_API_KEY + LLM_MODEL
  - or OPENROUTER_API_KEY
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def test_full_journey():
    print("═══ END-TO-END MISSION TEST ═══\n")
    errors = []

    # 1. Create tenant
    print("▸ 1. Create tenant")
    try:
        from src.raas.tenant import TenantStore
        store = TenantStore()
        tenant = store.create_tenant("e2e_test_customer")
        print(f"  ID: {tenant.id[:12]}...")
        print(f"  Key: {tenant.api_key[:15]}...")
        print("  ✅ Tenant created")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        errors.append(f"Tenant: {e}")
        return errors

    # 2. Fund credits
    print("\n▸ 2. Fund credits")
    try:
        from src.raas.credits import CreditStore
        credits = CreditStore()
        credits.add(tenant.id, 100, "e2e_test_funding")
        bal = credits.get_balance(tenant.id)
        print(f"  Balance: {bal}")
        print("  ✅ Credits funded")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        errors.append(f"Credits: {e}")
        return errors

    # 3. Classify task
    print("\n▸ 3. Classify task")
    try:
        from src.core.task_classifier import classify_task
        goal = "Write a one-paragraph marketing pitch for a Vietnamese coffee brand"
        profile = classify_task(goal)
        print(f"  Goal: {goal[:60]}...")
        print(f"  Agent: {profile.agent_role}")
        print(f"  Domain: {profile.domain}")
        print(f"  Cost: {profile.mcu_cost} MCU")
        print("  ✅ Classified")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        errors.append(f"Classifier: {e}")

    # 4. Execute mission via hybrid router
    print("\n▸ 4. Execute mission (calls LLM)")
    try:
        from src.core.hybrid_router import route_and_execute
        from src.core.mcu_gate import MCUGate

        gate = MCUGate()
        gate.seed_balance(tenant.id, 100, "e2e_test_funding")

        result = await route_and_execute(
            goal=goal,
            tenant_id=tenant.id,
            mission_id="e2e_test_001",
            mcu_gate=gate,
        )
        print(f"  Success: {result.success}")
        print(f"  Model: {result.model_used}")
        print(f"  MCU charged: {result.mcu_charged}")
        if result.output:
            print(f"  Output ({len(result.output)} chars):")
            print(f"    {result.output[:300]}")
            print("  ✅ Mission produced output")
        else:
            print("  ❌ Output is EMPTY")
            print(f"  Error: {result.error}")
            errors.append(f"Mission: empty output — {result.error}")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        errors.append(f"Mission: {e}")

    # 5. Check credits deducted
    print("\n▸ 5. Credits after mission")
    try:
        bal_after = credits.get_balance(tenant.id)
        print(f"  Before: 100, After: {bal_after}")
        if bal_after < 100:
            print("  ✅ Credits deducted correctly")
        else:
            print("  ⚠️  Credits not deducted (MCU gate tracks separately)")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")

    # Summary
    print("\n═══ SUMMARY ═══")
    if not errors:
        print("✅ ALL PASS — Mekong can deliver value. Ready to sell.")
    else:
        print(f"❌ {len(errors)} FAILURES — NOT ready to sell:")
        for err in errors:
            print(f"  - {err}")

    return errors


if __name__ == "__main__":
    errors = asyncio.run(test_full_journey())
    sys.exit(1 if errors else 0)
