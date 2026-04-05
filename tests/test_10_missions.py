"""Run 10 diverse missions to verify output quality.

Run with: python3 tests/test_10_missions.py

Requires at least one LLM provider configured.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

GOALS = [
    "Create an invoice template for a web development project",
    "Write a cold outreach email for a SaaS product",
    "Review this employment contract for red flags",
    "Design a 1-week social media content calendar",
    "Analyze monthly expenses and suggest 3 cost cuts",
    "Draft a project status update for stakeholders",
    "Create onboarding checklist for new developer",
    "Write a product description for AI writing tool",
    "Design database schema for customer support tickets",
    "Create a 90-day growth plan for a new startup",
]


async def run_all():
    from src.core.hybrid_router import route_and_execute
    from src.core.mcu_gate import MCUGate
    from src.raas.tenant import TenantStore

    store = TenantStore()
    tenant = store.create_tenant("quality_test")
    gate = MCUGate()
    gate.seed_balance(tenant.id, 500, "quality_test_funding")

    passed = 0
    for i, goal in enumerate(GOALS):
        try:
            result = await route_and_execute(
                goal=goal,
                tenant_id=tenant.id,
                mission_id=f"quality_{i}",
                mcu_gate=gate,
            )
            has_output = bool(result.output and len(result.output) > 50)
            status = "✅" if result.success and has_output else "❌"
            model = result.model_used or "none"
            chars = len(result.output or "")
            print(f"  {status} [{i+1}/10] {goal[:50]:50s} → {model:20s} {chars} chars")
            if result.success and has_output:
                passed += 1
        except Exception as e:
            print(f"  ❌ [{i+1}/10] {goal[:50]:50s} → CRASH: {e}")

    print(f"\n  Score: {passed}/10")
    if passed >= 8:
        print("  ✅ READY TO SELL")
    else:
        print("  ❌ NOT READY — fix failing missions first")

    return passed


if __name__ == "__main__":
    score = asyncio.run(run_all())
    sys.exit(0 if score >= 8 else 1)
