"""Mekong CLI - DocsAgent.

Auto-generates project documentation by scanning the codebase.
Follows the Plan-Execute-Verify pattern from AgentBase.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from ..core.agent_base import AgentBase, Result, Task


_DOC_SPECS = [
    ("codebase-summary", "High-level overview of the project structure"),
    ("code-standards", "Coding standards and conventions used"),
    ("system-architecture", "System architecture and component diagram"),
    ("api-reference", "API endpoints and their schemas"),
]


class DocsAgent(AgentBase):
    """Agent for automatic documentation generation.

    Scans source directories and generates structured
    documentation files in the docs/ output directory.
    """

    def __init__(self, workspace: str = ".", output_dir: str = "docs") -> None:
        """Initialize DocsAgent.

        Args:
            workspace: Root directory to scan.
            output_dir: Directory to write generated docs.
        """
        super().__init__(name="DocsAgent")
        self._workspace = Path(workspace).resolve()
        self._output_dir = self._workspace / output_dir

    def plan(self, input_data: str) -> List[Task]:
        """Generate documentation plan.

        Args:
            input_data: Command — 'init' generates all 4 doc specs,
                        or a specific doc name.

        Returns:
            List of documentation tasks.
        """
        if input_data.strip() == "init":
            return [
                Task(
                    id=f"doc_{name}",
                    description=f"Generate {name}: {desc}",
                    input={"name": name, "description": desc},
                )
                for name, desc in _DOC_SPECS
            ]

        # Single doc generation
        for name, desc in _DOC_SPECS:
            if name == input_data.strip():
                return [
                    Task(
                        id=f"doc_{name}",
                        description=f"Generate {name}: {desc}",
                        input={"name": name, "description": desc},
                    )
                ]

        return [
            Task(
                id="doc_unknown",
                description=f"Unknown doc type: {input_data}",
                input={"name": input_data, "description": ""},
            )
        ]

    def execute(self, task: Task) -> Result:
        """Scan targets and generate documentation.

        Args:
            task: Documentation generation task.

        Returns:
            Result with generated file path or error.
        """
        name: str = task.input.get("name", "unknown")
        desc: str = task.input.get("description", "")

        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            content = self._generate_content(name, desc)
            out_path = self._output_dir / f"{name}.md"
            out_path.write_text(content, encoding="utf-8")

            return Result(
                task_id=task.id,
                success=True,
                output=str(out_path),
            )
        except Exception as e:
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error=str(e),
            )

    def verify(self, result: Result) -> bool:
        """Check all generated files exist.

        Args:
            result: Result from execute().

        Returns:
            True if the output file exists.
        """
        if not result.success or not result.output:
            return False
        return Path(str(result.output)).is_file()

    def _generate_content(self, name: str, description: str) -> str:
        """Generate markdown content by scanning the workspace.

        Args:
            name: Document type identifier.
            description: Human-readable description.

        Returns:
            Generated markdown string.
        """
        generators = {
            "codebase-summary": self._gen_codebase_summary,
            "code-standards": self._gen_code_standards,
            "system-architecture": self._gen_system_architecture,
            "api-reference": self._gen_api_reference,
        }

        generator = generators.get(name)
        if generator:
            return generator()

        return f"# {name}\n\n{description}\n"

    def _gen_codebase_summary(self) -> str:
        """Generate codebase summary by scanning directories."""
        lines = ["# Codebase Summary\n"]
        src = self._workspace / "src"
        if src.is_dir():
            for entry in sorted(src.iterdir()):
                if entry.is_dir() and not entry.name.startswith("_"):
                    py_count = len(list(entry.glob("*.py")))
                    lines.append(f"- **{entry.name}/**: {py_count} Python modules")
        return "\n".join(lines) + "\n"

    def _gen_code_standards(self) -> str:
        """Generate code standards document."""
        return (
            "# Code Standards\n\n"
            "- Type hints on all functions\n"
            "- Docstrings on all public classes and methods\n"
            "- File size < 200 lines\n"
            "- snake_case for functions, PascalCase for classes\n"
            "- Conventional commits: feat/fix/refactor/docs/test/chore\n"
        )

    def _gen_system_architecture(self) -> str:
        """Generate system architecture overview."""
        lines = ["# System Architecture\n", "## Components\n"]
        src = self._workspace / "src"
        if src.is_dir():
            for entry in sorted(src.iterdir()):
                if entry.is_dir() and not entry.name.startswith("_"):
                    lines.append(f"### {entry.name}")
                    init = entry / "__init__.py"
                    if init.is_file():
                        first_line = init.read_text(errors="ignore").split("\n")[0]
                        if first_line.startswith('"""'):
                            lines.append(first_line.strip('"'))
                    lines.append("")
        return "\n".join(lines) + "\n"

    def _gen_api_reference(self) -> str:
        """Generate API reference by scanning for FastAPI routers."""
        lines = ["# API Reference\n"]
        api_dir = self._workspace / "src" / "api"
        if api_dir.is_dir():
            for py_file in sorted(api_dir.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                lines.append(f"## {py_file.stem}")
                lines.append(f"Source: `src/api/{py_file.name}`\n")
        else:
            lines.append("No API directory found.\n")
        return "\n".join(lines) + "\n"


__all__ = ["DocsAgent"]
