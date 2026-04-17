#!/usr/bin/env python3
"""
Mekong CLI Command Audit Script
Compares .claude/commands/**/*.md specs vs src/commands/*.py live modules.

Usage:
    python3 docs/command-audit/audit-script.py [--root <project_root>]

Outputs:
    docs/command-audit/live-commands.md
    docs/command-audit/spec-only-commands.md
    docs/command-audit/ghost-commands.md
    docs/command-audit/mapping-table.csv
    .claude/commands/_audit.md
"""

import os
import sys
import csv
import argparse
from datetime import date
from collections import Counter


def find_py_modules(commands_dir: str) -> dict[str, str]:
    """Return {module_name: relative_path} for non-private Python modules."""
    result = {}
    if not os.path.isdir(commands_dir):
        return result
    for fname in os.listdir(commands_dir):
        if fname.endswith(".py") and not fname.startswith("_"):
            name = fname[:-3]
            result[name] = os.path.join(commands_dir, fname)
    return result


def find_spec_files(commands_dir: str) -> list[tuple[str, str]]:
    """Return [(spec_name, relative_path)] for non-private markdown files."""
    result = []
    for root, _, files in os.walk(commands_dir):
        for fname in sorted(files):
            if fname.endswith(".md") and not fname.startswith("_"):
                name = fname[:-3]
                full_path = os.path.join(root, fname)
                result.append((name, full_path))
    return result


def infer_tier(spec_path: str) -> str:
    """Infer CLAUDE.md layer tier from path or name."""
    path_lower = spec_path.lower()
    name = os.path.basename(spec_path)[:-3]

    if any(x in name for x in ["studio", "dealflow", "venture", "expert"]):
        return "studio"
    if any(x in name for x in ["annual", "okr", "fundraise", "swot", "pitch", "ipo", "vc", "board", "cap-table"]):
        return "founder"
    if any(x in name for x in ["sales", "marketing", "finance", "hr", "pricing", "brand", "crm", "accounting",
                                 "ae-", "outreach", "client", "business-"]):
        return "business"
    if any(x in name for x in ["plan", "sprint", "roadmap", "brainstorm", "scope", "product", "prd", "backlog"]):
        return "product"
    if any(x in name for x in ["cook", "code", "test", "deploy", "build", "ci", "lint", "review",
                                 "debug", "fix", "refactor", "tdd", "sdlc", "backend", "api"]):
        return "engineering"
    if any(x in name for x in ["audit", "health", "security", "status", "clean", "monitor",
                                 "ops", "compliance", "legal", "raas", "ocop", "sync", "telemetry"]):
        return "ops"
    # subdirectory hints
    if "/raas/" in path_lower:
        return "ops"
    if "/ci/" in path_lower or "/sdlc/" in path_lower or "/code/" in path_lower:
        return "engineering"
    if "/finance/" in path_lower:
        return "business"
    if "/git/" in path_lower:
        return "engineering"
    if "/tasks/" in path_lower or "/context/" in path_lower:
        return "product"
    return "misc"


def build_audit(root: str) -> dict:
    """Run full audit and return data dict."""
    spec_dir = os.path.join(root, ".claude", "commands")
    py_dir = os.path.join(root, "src", "commands")

    py_modules = find_py_modules(py_dir)  # {module_name: path}
    spec_files = find_spec_files(spec_dir)  # [(spec_name, path)]

    py_set = set(py_modules.keys())

    rows = []  # (command_name, spec_path, module_path, status, tier)
    matched_py = set()

    for spec_name, spec_path in spec_files:
        snake = spec_name.replace("-", "_")
        rel_spec = os.path.relpath(spec_path, root)
        tier = infer_tier(rel_spec)

        if snake in py_set:
            mod_path = os.path.relpath(py_modules[snake], root)
            rows.append((spec_name, rel_spec, mod_path, "LIVE", tier))
            matched_py.add(snake)
        elif spec_name in py_set:
            mod_path = os.path.relpath(py_modules[spec_name], root)
            rows.append((spec_name, rel_spec, mod_path, "LIVE", tier))
            matched_py.add(spec_name)
        else:
            rows.append((spec_name, rel_spec, "", "SPEC_ONLY", tier))

    # Ghost: py modules with no spec
    for py_name, py_path in sorted(py_modules.items()):
        if py_name not in matched_py:
            rel_py = os.path.relpath(py_path, root)
            tier = infer_tier(py_name)
            rows.append((py_name, "", rel_py, "GHOST", tier))

    counts = Counter(r[3] for r in rows)
    return {
        "rows": rows,
        "counts": counts,
        "spec_total": len(spec_files),
        "py_total": len(py_modules),
    }


def write_csv(rows: list, out_path: str) -> None:
    """Write mapping-table.csv."""
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["command_name", "spec_path", "module_path", "status", "tier"])
        for row in sorted(rows, key=lambda r: (r[3], r[0])):
            w.writerow(row)


def write_live_md(rows: list, out_path: str, audit_date: str) -> None:
    live = [r for r in rows if r[3] == "LIVE"]
    # Deduplicate by module (multiple specs may map same module)
    seen = set()
    unique_live = []
    for r in live:
        key = r[2]  # module_path
        if key not in seen:
            seen.add(key)
            unique_live.append(r)

    lines = [
        f"# Live Commands — Verified Executable",
        f"",
        f"> Audit date: {audit_date}",
        f"> Definition: Python module exists in `src/commands/` with matching spec name.",
        f"",
        f"**Total live modules: {len(unique_live)}** (unique Python files)",
        f"**Total live spec entries: {len(live)}** (some modules have multiple specs across subdirs)",
        f"",
        f"| # | Command | Spec Path | Module Path | Tier |",
        f"|---|---------|-----------|-------------|------|",
    ]
    for i, r in enumerate(sorted(unique_live, key=lambda x: x[0]), 1):
        lines.append(f"| {i} | `{r[0]}` | `{r[1]}` | `{r[2]}` | {r[4]} |")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_spec_only_md(rows: list, out_path: str, audit_date: str) -> None:
    spec_only = [r for r in rows if r[3] == "SPEC_ONLY"]
    lines = [
        f"# Spec-Only Commands — Markdown Defined, No Python Module",
        f"",
        f"> Audit date: {audit_date}",
        f"> Definition: `.claude/commands/**/*.md` exists but no matching `src/commands/*.py`.",
        f"> These are aspirational specs or CC CLI pass-through commands (no Python backend needed).",
        f"",
        f"**Total spec-only: {len(spec_only)}**",
        f"",
        f"| # | Command | Spec Path | Tier |",
        f"|---|---------|-----------|------|",
    ]
    for i, r in enumerate(sorted(spec_only, key=lambda x: (x[4], x[0])), 1):
        lines.append(f"| {i} | `{r[0]}` | `{r[1]}` | {r[4]} |")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_ghost_md(rows: list, out_path: str, audit_date: str) -> None:
    ghost = [r for r in rows if r[3] == "GHOST"]
    lines = [
        f"# Ghost Commands — Python Module Exists, No Markdown Spec",
        f"",
        f"> Audit date: {audit_date}",
        f"> Definition: `src/commands/*.py` exists but no corresponding `.claude/commands/**/*.md`.",
        f"> These are implementation-only modules: either internal helpers or undocumented commands.",
        f"",
        f"**Total ghost: {len(ghost)}**",
        f"",
        f"| # | Module Name | Module Path | Tier |",
        f"|---|-------------|-------------|------|",
    ]
    for i, r in enumerate(sorted(ghost, key=lambda x: x[0]), 1):
        lines.append(f"| {i} | `{r[0]}` | `{r[2]}` | {r[4]} |")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_audit_index_md(data: dict, out_path: str, audit_date: str) -> None:
    counts = data["counts"]
    live_unique = len(set(r[2] for r in data["rows"] if r[3] == "LIVE"))
    lines = [
        f"---",
        f"audit_date: {audit_date}",
        f"spec_count: {data['spec_total']}",
        f"py_module_count: {data['py_total']}",
        f"live: {live_unique}",
        f"spec_only: {counts['SPEC_ONLY']}",
        f"ghost: {counts['GHOST']}",
        f"---",
        f"",
        f"# Command Audit Index",
        f"",
        f"Last run: **{audit_date}**",
        f"",
        f"## Counts",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Markdown specs (`.claude/commands/**/*.md`) | {data['spec_total']} |",
        f"| Python modules (`src/commands/*.py`) | {data['py_total']} |",
        f"| LIVE (spec + module match, unique modules) | {live_unique} |",
        f"| SPEC_ONLY (spec, no module) | {counts['SPEC_ONLY']} |",
        f"| GHOST (module, no spec) | {counts['GHOST']} |",
        f"",
        f"## Gap vs README Claim",
        f"",
        f"README claims: **443 commands**",
        f"Audited live (unique Python modules): **{live_unique}**",
        f"Gap: **{443 - live_unique}** commands are spec-only or ghost (not end-to-end shipped)",
        f"",
        f"## Links",
        f"",
        f"- [Audit README](docs/command-audit/README.md)",
        f"- [Live Commands](docs/command-audit/live-commands.md)",
        f"- [Spec-Only Commands](docs/command-audit/spec-only-commands.md)",
        f"- [Ghost Commands](docs/command-audit/ghost-commands.md)",
        f"- [Mapping Table CSV](docs/command-audit/mapping-table.csv)",
    ]
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Mekong CLI command audit")
    parser.add_argument("--root", default=".", help="Project root (default: cwd)")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    audit_date = str(date.today())
    out_dir = os.path.join(root, "docs", "command-audit")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[audit] Root: {root}")
    print(f"[audit] Date: {audit_date}")

    data = build_audit(root)
    counts = data["counts"]
    live_unique = len(set(r[2] for r in data["rows"] if r[3] == "LIVE"))

    print(f"[audit] Spec files: {data['spec_total']}")
    print(f"[audit] Python modules: {data['py_total']}")
    print(f"[audit] LIVE (unique): {live_unique}")
    print(f"[audit] SPEC_ONLY: {counts['SPEC_ONLY']}")
    print(f"[audit] GHOST: {counts['GHOST']}")

    write_csv(data["rows"], os.path.join(out_dir, "mapping-table.csv"))
    write_live_md(data["rows"], os.path.join(out_dir, "live-commands.md"), audit_date)
    write_spec_only_md(data["rows"], os.path.join(out_dir, "spec-only-commands.md"), audit_date)
    write_ghost_md(data["rows"], os.path.join(out_dir, "ghost-commands.md"), audit_date)
    write_audit_index_md(data, os.path.join(root, ".claude", "commands", "_audit.md"), audit_date)

    print(f"[audit] Outputs written to {out_dir}/")
    print(f"[audit] Gap vs README (443 claimed): {443 - live_unique} commands unshipped")


if __name__ == "__main__":
    main()
