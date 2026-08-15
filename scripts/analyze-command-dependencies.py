#!/usr/bin/env python3
"""Analyze command module dependencies and complexity.

This script scans src/commands/ to produce:
- Command count per module and layer
- Complexity metrics (lines, imports, functions)
- Dependency graph between modules
- Migration priority scoring
- Hotspot identification

Output: JSON report + Markdown summary
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class ModuleAnalysis:
    """Analysis results for a single command module."""
    path: str
    layer: str
    line_count: int
    command_count: int
    function_count: int
    import_count: int
    typer_app: str | None
    dependencies: list[str]
    complexity_score: float  # 0-100, higher = more complex

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CommandAnalyzer:
    """Analyze command modules."""

    def __init__(self, commands_dir: Path | None = None) -> None:
        self.commands_dir = commands_dir or project_root / "src" / "commands"
        self.modules: list[ModuleAnalysis] = []

    def analyze_all(self) -> list[ModuleAnalysis]:
        """Analyze all command modules."""
        if not self.commands_dir.exists():
            print(f"Error: {self.commands_dir} not found")
            return []

        for module_file in sorted(self.commands_dir.glob("*.py")):
            if module_file.name.startswith("_"):
                continue

            analysis = self._analyze_module(module_file)
            if analysis:
                self.modules.append(analysis)

        return self.modules

    def _analyze_module(self, path: Path) -> ModuleAnalysis | None:
        """Analyze a single module."""
        try:
            content = path.read_text()
        except Exception as e:
            print(f"Warning: Cannot read {path}: {e}")
            return None

        lines = content.count("\n") + 1
        layer = self._detect_layer(path, content)
        commands = self._count_commands(content)
        functions = self._count_functions(content)
        imports = self._extract_imports(content)
        typer_app = self._find_typer_app(content)

        # Calculate complexity score
        score = self._calculate_complexity(
            lines=lines,
            commands=commands,
            functions=functions,
            imports=len(imports),
        )

        # Detect dependencies
        deps = self._infer_dependencies(imports, layer)

        return ModuleAnalysis(
            path=str(path.relative_to(project_root)),
            layer=layer,
            line_count=lines,
            command_count=commands,
            function_count=functions,
            import_count=len(imports),
            typer_app=typer_app,
            dependencies=deps,
            complexity_score=score,
        )

    def _detect_layer(self, path: Path, content: str) -> str:
        """Detect business layer."""
        path_str = str(path).lower()
        layer_mapping = {
            "founder": ["founder", "annual", "okr", "swot", "fundraise"],
            "business": ["business", "sales", "marketing", "finance", "hr"],
            "product": ["product", "plan", "sprint", "roadmap"],
            "engineering": ["engineering", "cook", "code", "test", "deploy"],
            "ops": ["ops", "audit", "health", "security"],
            "studio": ["studio", "venture", "dealflow"],
        }
        for layer, keywords in layer_mapping.items():
            if any(kw in path_str for kw in keywords) or any(kw in content.lower() for kw in keywords):
                return layer
        return "engineering"

    def _count_commands(self, content: str) -> int:
        """Count Typer commands."""
        pattern = r'@(?:\w+\.)?command\('
        return len(re.findall(pattern, content))

    def _count_functions(self, content: str) -> int:
        """Count function definitions."""
        pattern = r'^def\s+\w+\s*\('
        return len(re.findall(pattern, content, re.MULTILINE))

    def _extract_imports(self, content: str) -> list[str]:
        """Extract all imports."""
        imports = []
        for match in re.finditer(r'from\s+([^\s]+)\s+import', content):
            imports.append(match.group(1))
        for match in re.finditer(r'import\s+([^\s,]+)', content):
            imports.append(match.group(1))
        return sorted(set(imports))

    def _find_typer_app(self, content: str) -> str | None:
        """Find Typer app variable."""
        match = re.search(r'(\w+)\s*=\s*typer\.Typer\(', content)
        return match.group(1) if match else None

    def _calculate_complexity(self, lines: int, commands: int, functions: int, imports: int) -> float:
        """Calculate complexity score 0-100."""
        # Weighted factors
        score = (
            (lines / 200) * 30 +  # Lines of code (max 30)
            (commands / 5) * 25 +  # Number of commands (max 25)
            (functions / 10) * 20 +  # Functions (max 20)
            (imports / 10) * 15 +  # Imports (max 15)
            (1 if lines > 300 else 0) * 10  # Large file penalty (max 10)
        )
        return min(score, 100.0)

    def _infer_dependencies(self, imports: list[str], layer: str) -> list[str]:
        """Infer plugin dependencies."""
        deps = []
        mapping = {
            "src.services": "mekong-core-services",
            "src.agents": "mekong-core-agents",
            "src.core": "mekong-core-orchestrator",
        }
        for imp in imports:
            for key, plugin in mapping.items():
                if imp.startswith(key) and plugin not in deps:
                    deps.append(plugin)
        return deps

    def generate_report(self, output_dir: Path) -> None:
        """Generate analysis reports."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # JSON report
        json_data = {
            "generated": "auto",
            "total_modules": len(self.modules),
            "total_commands": sum(m.command_count for m in self.modules),
            "by_layer": {},
            "modules": [m.to_dict() for m in self.modules],
        }

        # Group by layer
        for layer in sorted(set(m.layer for m in self.modules)):
            layer_mods = [m for m in self.modules if m.layer == layer]
            json_data["by_layer"][layer] = {
                "modules": len(layer_mods),
                "commands": sum(m.command_count for m in layer_mods),
                "avg_complexity": sum(m.complexity_score for m in layer_mods) / len(layer_mods) if layer_mods else 0,
            }

        json_path = output_dir / "command-analysis.json"
        json_path.write_text(json.dumps(json_data, indent=2))

        # Markdown summary
        md = self._generate_markdown(json_data)
        md_path = output_dir / "command-analysis.md"
        md_path.write_text(md)

        print(f"✅ Analysis complete: {output_dir}/")
        print(f"   - {json_path.name}")
        print(f"   - {md_path.name}")
        print(f"\n📊 Total: {len(self.modules)} modules, {json_data['total_commands']} commands")

    def _generate_markdown(self, data: dict[str, Any]) -> str:
        """Generate markdown report."""
        lines = [
            "# Command Module Analysis",
            "",
            "**Generated**: auto",
            f"**Total Modules**: {data['total_modules']}",
            f"**Total Commands**: {data['total_commands']}",
            "",
            "## By Layer",
            "",
            "| Layer | Modules | Commands | Avg Complexity |",
            "|-------|---------|----------|----------------|",
        ]

        for layer, stats in sorted(data["by_layer"].items()):
            lines.append(f"| {layer} | {stats['modules']} | {stats['commands']} | {stats['avg_complexity']:.1f} |")

        lines.extend([
            "",
            "## Top 10 Most Complex Modules",
            "",
            "| Module | Layer | Lines | Commands | Complexity |",
            "|--------|-------|-------|----------|------------|",
        ])

        sorted_mods = sorted(data["modules"], key=lambda m: m["complexity_score"], reverse=True)
        for mod in sorted_mods[:10]:
            lines.append(f"| {mod['path']} | {mod['layer']} | {mod['line_count']} | {mod['command_count']} | {mod['complexity_score']:.1f} |")

        lines.extend([
            "",
            "## Migration Recommendations",
            "",
            "- **High Priority** (simple, high-use): Migrate first (v6.2-v6.3)",
            "- **Medium Priority** (medium complexity): Migrate v6.4-v6.5",
            "- **Low Priority** (complex, low-use): Migrate v6.6-v6.7",
            "",
            "See `incremental-migration-strategy.md` for full plan.",
        ])

        return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze command modules")
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "build" / "command-analysis",
        help="Output directory",
    )
    args = parser.parse_args()

    analyzer = CommandAnalyzer()
    modules = analyzer.analyze_all()

    if not modules:
        print("No modules found or analyzed")
        return 1

    analyzer.generate_report(args.output)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
