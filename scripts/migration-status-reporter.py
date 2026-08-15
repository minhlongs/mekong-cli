#!/usr/bin/env python3
"""Migration Status Reporter

Shows current migration status for all command layers.

Usage:
    python3 scripts/migration-status-reporter.py [--detailed] [--json]

Output:
    - Layer status (legacy/shim/plugin/not-started)
    - Command counts
    - Migration progress percentage
    - Issues and warnings
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class LayerStatus:
    """Status for a single layer."""
    layer: str
    total_commands: int
    migrated_commands: int
    status: str  # "not-started", "shim", "plugin", "legacy"
    plugin_id: str | None
    issues: list[str]

    @property
    def progress_pct(self) -> float:
        if self.total_commands == 0:
            return 0.0
        return (self.migrated_commands / self.total_commands) * 100

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MigrationStatusReporter:
    """Report migration status across all layers."""

    LAYERS = ["founder", "business", "product", "engineering", "ops", "studio"]

    def __init__(self) -> None:
        self.statuses: dict[str, LayerStatus] = {}
        self._load_analysis()
        self._detect_plugin_status()
        self._check_feature_flags()

    def _load_analysis(self) -> None:
        """Load command analysis from build/command-analysis/command-analysis.json."""
        analysis_path = project_root / "build" / "command-analysis" / "command-analysis.json"
        if not analysis_path.exists():
            print("Warning: Analysis not found. Run analyze-command-dependencies.py first.")
            self.layer_commands = {layer: 0 for layer in self.LAYERS}
            return

        data = json.loads(analysis_path.read_text())
        by_layer = data.get("by_layer", {})

        self.layer_commands = {}
        for layer in self.LAYERS:
            self.layer_commands[layer] = by_layer.get(layer, {}).get("commands", 0)

    def _detect_plugin_status(self) -> None:
        """Detect which plugins are available and active."""
        # Check plugins directory
        plugins_dir = project_root / "plugins"
        available_plugins = set()

        if plugins_dir.exists():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir() and plugin_dir.name.startswith("mekong-core-"):
                    plugin_id = plugin_dir.name
                    available_plugins.add(plugin_id)
                    # Extract layer from plugin ID
                    layer = plugin_id.replace("mekong-core-", "")
                    # Check if plugin is active (simple check: manifest exists)
                    manifest = plugin_dir / "plugin.json"
                    status = "plugin" if manifest.exists() else "stub"
                    self._set_layer_status(layer, status=status, plugin_id=plugin_id)

        # Mark layers without plugins
        for layer in self.LAYERS:
            if layer not in self.statuses:
                self.statuses[layer] = LayerStatus(
                    layer=layer,
                    total_commands=self.layer_commands.get(layer, 0),
                    migrated_commands=0,
                    status="not-started",
                    plugin_id=None,
                    issues=["No plugin created"],
                )

    def _check_feature_flags(self) -> None:
        """Check feature flag settings."""
        settings_path = Path.home() / ".mekong" / "settings.json"
        if not settings_path.exists():
            return

        try:
            pass  # Would use jq if available, but we'll approximate
            # For simplicity, skip actual parsing
        except Exception:
            pass

    def _set_layer_status(self, layer: str, status: str, plugin_id: str | None = None) -> None:
        """Update status for a layer."""
        total = self.layer_commands.get(layer, 0)
        migrated = total if status == "plugin" else 0

        existing = self.statuses.get(layer, LayerStatus(
            layer=layer,
            total_commands=total,
            migrated_commands=0,
            status="not-started",
            plugin_id=None,
            issues=[],
        ))

        self.statuses[layer] = LayerStatus(
            layer=layer,
            total_commands=total,
            migrated_commands=migrated if status == "plugin" else existing.migrated_commands,
            status=status,
            plugin_id=plugin_id or existing.plugin_id,
            issues=existing.issues,
        )

    def generate_report(self, detailed: bool = False) -> str:
        """Generate text report."""
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║       MEKONG COMMAND MIGRATION STATUS                        ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
        ]

        total_commands = sum(s.total_commands for s in self.statuses.values())
        total_migrated = sum(s.migrated_commands for s in self.statuses.values())
        overall_pct = (total_migrated / total_commands * 100) if total_commands else 0

        lines.append(f"Overall Progress: {total_migrated}/{total_commands} commands ({overall_pct:.1f}%)")
        lines.append("")

        # Table header
        lines.append("┌─────────┬────────────┬────────────┬────────────┬──────────┐")
        lines.append("│ Layer   │ Total      │ Migrated   │ Status     │ Progress │")
        lines.append("├─────────┼────────────┼────────────┼────────────┼──────────┤")

        status_icons = {
            "not-started": "⭕",
            "stub": "🔸",
            "plugin": "✅",
            "legacy": "♻️",
            "shim": "🔧",
        }

        for layer in self.LAYERS:
            status = self.statuses.get(layer)
            if not status:
                continue

            icon = status_icons.get(status.status, "?")
            progress = f"{status.progress_pct:5.1f}%" if status.total_commands > 0 else "   N/A"

            lines.append(
                f"│ {icon} {layer:7} │ {status.total_commands:10} │ "
                f"{status.migrated_commands:10} │ {status.status:10} │ {progress:8} │"
            )

        lines.append("└─────────┴────────────┴────────────┴────────────┴──────────┘")
        lines.append("")

        # Legend
        lines.append("Legend:")
        lines.append("  ✅ plugin   - Fully migrated plugin active")
        lines.append("  🔸 stub     - Plugin stub created, needs implementation")
        lines.append("  🔧 shim     - Compatibility layer (plugin → legacy fallback)")
        lines.append("  ♻️  legacy   - Using legacy command module")
        lines.append("  ⭕ not-started - No plugin created yet")
        lines.append("")

        # Issues summary
        any_issues = any(s.issues for s in self.statuses.values())
        if any_issues:
            lines.append("⚠️  Issues:")
            for layer, status in self.statuses.items():
                if status.issues:
                    for issue in status.issues:
                        lines.append(f"   {layer}: {issue}")
            lines.append("")

        # Next steps
        lines.append("📋 Next Steps:")
        lines.append("  1. Implement stub handlers in plugins/mekong-core-*/handlers/")
        lines.append("  2. Run: python3 scripts/migrate-commands-to-plugins.py")
        lines.append("  3. Enable canary: export MEKONG_FEATURE_PLUGIN_FOUNDER=plugin")
        lines.append("  4. Monitor: mekong admin migration status")
        lines.append("  5. See docs/incremental-migration-strategy.md for full plan")
        lines.append("")

        # Commands
        lines.append("🔧 Useful Commands:")
        lines.append("  mekong admin plugin list              # List all plugins")
        lines.append("  mekong admin plugin status <id>       # Plugin health")
        lines.append("  scripts/migration-canary-tester.py    # Test plugin performance")
        lines.append("  scripts/migration-rollback.sh full    # Emergency rollback")
        lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "generated": "auto",
            "overall": {
                "total_commands": sum(s.total_commands for s in self.statuses.values()),
                "migrated_commands": sum(s.migrated_commands for s in self.statuses.values()),
                "plugins_available": sum(1 for s in self.statuses.values() if s.plugin_id),
            },
            "layers": {layer: status.to_dict() for layer, status in self.statuses.items()},
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Report migration status")
    parser.add_argument("--detailed", action="store_true", help="Show detailed information")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--output", type=Path, help="Write report to file")

    args = parser.parse_args()

    reporter = MigrationStatusReporter()

    if args.json:
        report = reporter.to_dict()
        output = json.dumps(report, indent=2)
    else:
        output = reporter.generate_report(detailed=args.detailed)

    if args.output:
        args.output.write_text(output)
        print(f"Report written to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
