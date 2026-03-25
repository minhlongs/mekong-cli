"""Mekong CLI - Documentation commands.

Commands:
  mekong docs init   — Scan codebase, generate all docs
  mekong docs update — Update existing docs
"""

from __future__ import annotations

import sys
from pathlib import Path


def _get_agent() -> object:
    """Lazy-import DocsAgent to avoid heavy import chain."""
    from src.agents.docs_agent import DocsAgent
    return DocsAgent()


def docs_init(workspace: str = ".") -> int:
    """Scan codebase and generate all documentation.

    Args:
        workspace: Root directory to scan.

    Returns:
        Exit code (0 = success).
    """
    from src.agents.docs_agent import DocsAgent

    agent = DocsAgent(workspace=workspace)
    results = agent.run("init")
    failures = [r for r in results if not r.success]

    for r in results:
        status = "OK" if r.success else "FAIL"
        print(f"  [{status}] {r.task_id}: {r.output or r.error}")

    if failures:
        print(f"\n{len(failures)} doc(s) failed to generate.")
        return 1

    print(f"\n{len(results)} docs generated in docs/")
    return 0


def docs_update(workspace: str = ".") -> int:
    """Update existing documentation.

    Re-runs init to regenerate all docs with current state.

    Args:
        workspace: Root directory to scan.

    Returns:
        Exit code (0 = success).
    """
    return docs_init(workspace)


def main() -> None:
    """CLI entry point for docs commands."""
    args = sys.argv[1:] if len(sys.argv) > 1 else ["init"]
    command = args[0] if args else "init"
    workspace = args[1] if len(args) > 1 else "."

    commands = {
        "init": docs_init,
        "update": docs_update,
    }

    handler = commands.get(command)
    if handler is None:
        print(f"Unknown command: {command}")
        print("Usage: mekong docs [init|update]")
        sys.exit(1)

    sys.exit(handler(workspace))


if __name__ == "__main__":
    main()
