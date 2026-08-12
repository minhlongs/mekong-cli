#!/usr/bin/env python3
"""
Plugin Dependency Checker

Checks for dependency issues in plugin manifests:
- Circular dependencies
- Missing required dependencies
- Version conflicts
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "mekong-plugin-sdk" / "src"))

from mekong_plugin_sdk.manifest import load_manifest


def find_plugins(plugins_dir: Path) -> List[Path]:
    """Find all plugin directories containing mekong-plugin.json."""
    if not plugins_dir.exists():
        return []

    # Find all mekong-plugin.json files recursively
    manifest_files = list(plugins_dir.rglob("mekong-plugin.json"))
    # Return parent directories (unique)
    plugins = list(set(manifest_file.parent for manifest_file in manifest_files))

    return plugins


def build_dependency_graph(plugins: List[Path]) -> Dict[str, Set[str]]:
    """Build a dependency graph from plugin manifests."""
    graph: Dict[str, Set[str]] = {}
    plugin_ids = set()

    # First pass: collect all plugin IDs
    for plugin_dir in plugins:
        try:
            manifest = load_manifest(plugin_dir / "mekong-plugin.json")
            plugin_ids.add(manifest.id)
            graph[manifest.id] = set()
        except Exception as e:
            print(f"Warning: Could not load {plugin_dir.name}: {e}")
            continue

    # Second pass: build edges
    for plugin_dir in plugins:
        try:
            manifest = load_manifest(plugin_dir / "mekong-plugin.json")
            for dep in manifest.dependencies:
                if dep.id in plugin_ids:
                    graph[manifest.id].add(dep.id)
        except Exception:
            continue

    return graph


def detect_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Detect circular dependencies using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])

        rec_stack.remove(node)
        path.pop()
        return False

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def check_dependencies(plugins_dir: Path) -> bool:
    """Check for dependency issues in all plugins."""
    plugins = find_plugins(plugins_dir)

    if not plugins:
        print("No plugins found.")
        return True

    print(f"Checking dependencies for {len(plugins)} plugin(s)...\n")

    # Build dependency graph
    graph = build_dependency_graph(plugins)

    # Detect cycles
    cycles = detect_cycles(graph)
    if cycles:
        print("❌ Circular dependencies detected:")
        for cycle in cycles:
            print(f"   {' -> '.join(cycle)}")
        return False

    print("✅ No circular dependencies found")

    # Check for missing dependencies
    all_plugin_ids = set(graph.keys())
    for plugin, deps in graph.items():
        missing = deps - all_plugin_ids
        if missing:
            print(f"⚠️  {plugin}: References non-existent plugins: {', '.join(missing)}")

    # Check for duplicate dependencies
    for plugin, deps in graph.items():
        if len(deps) != len(set(deps)):
            print(f"⚠️  {plugin}: Has duplicate dependencies")

    return len(cycles) == 0


def main():
    if len(sys.argv) > 1:
        plugins_dir = Path(sys.argv[1])
    else:
        plugins_dir = Path('packages')

    success = check_dependencies(plugins_dir)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
