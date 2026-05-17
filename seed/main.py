"""Entry point: python seed/main.py "your task here"."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seed.agents.ceo import CEOAgent
from seed.agents.developer import DeveloperAgent
from seed.agents.tester import TesterAgent
from seed.llm_client import get_llm_client

MAX_RETRIES = 2


def run(task: str) -> dict:
    print(f"\n🌱 Seed Agent starting...")
    print(f"📋 Task: {task}\n")

    llm = get_llm_client()
    if not llm.is_available():
        print("❌ Ollama không khả dụng. Hãy chạy: ollama serve")
        sys.exit(1)

    print("✅ Ollama connected\n")

    # CEO: plan
    ceo = CEOAgent()
    plan_data = ceo.create_plan(task)
    plan = plan_data.get("plan", [task])

    print(f"\n📝 Plan ({len(plan)} steps):")
    for i, step in enumerate(plan, 1):
        print(f"  {i}. {step}")
    print()

    developer = DeveloperAgent()
    tester = TesterAgent()

    # Dev → Test loop
    for attempt in range(1, MAX_RETRIES + 1):
        outputs = developer.execute_plan(plan, task)
        result = tester.verify(task, outputs)
        if result.get("passed", True):
            break
        issues = result.get("issues", [])
        print(f"\n  ⚠️  Attempt {attempt}: tester found {len(issues)} issue(s). Retrying...")
        plan = [f"Fix issues: {', '.join(issues[:3])}. Original task: {task}"]

    print("\n✨ Done! Outputs:")
    for out in outputs:
        print(f"  → {out}")
    print()

    return {"task": task, "plan": plan, "outputs": outputs, "test_result": result}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python seed/main.py \"your task here\"")
        sys.exit(1)
    task = " ".join(sys.argv[1:])
    run(task)


if __name__ == "__main__":
    main()
