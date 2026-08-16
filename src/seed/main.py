# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Seed main pipeline — CEO→Developer→Tester loop (config-driven via AgentFactory)."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from harness.agents.factory import get_factory
from seed.agents.base import get_llm_client

MAX_RETRIES = 3
AGENT_IDS = ("ceo", "eng", "tester")


def _load_factory() -> Any:
    """Return singleton AgentFactory, loading config from project root."""
    config = str(Path(__file__).resolve().parents[2] / "agents" / "registry.yaml")
    return get_factory(config)


def run(task: str) -> dict[str, Any]:
    """Execute task through plan→develop→test loop via factory."""
    llm = get_llm_client()
    if llm and not llm.is_available():
        sys.exit(1)
    factory = _load_factory()
    ceo = factory.create("ceo", llm=llm)
    dev = factory.create("eng", llm=llm)
    tester = factory.create("tester", llm=llm)

    plan_result = ceo.create_plan(task)
    plan = plan_result.get("plan", [task])

    outputs: list[str] = []
    last_test: dict[str, Any] = {}

    for attempt in range(MAX_RETRIES):
        outputs = dev.execute_plan(plan)
        last_test = tester.verify(task, outputs)
        if last_test.get("passed", False):
            break

    return {
        "task": task,
        "plan": plan,
        "outputs": outputs,
        "test_result": last_test,
    }


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: seed <task>")
        sys.exit(1)
    result = run(sys.argv[1])
    print(result)
