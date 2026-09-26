#!/usr/bin/env python3
# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Audit all Antigravity skills and classify their CLI mapping.

Produces reports/antigravity_audit.json with:
- skill name
- extracted mekong command from SKILL.md
- classification: executable | sub-command | antigravity-only
- CLI exit code from --help probe
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROJECT_ROOT / ".agents" / "skills"
REPORT_PATH = PROJECT_ROOT / "reports" / "antigravity_audit.json"

# Skills that are Antigravity-native with no CLI backend
ANTIGRAVITY_ONLY_SKILLS = {
    "agy", "agy-customizations", "ai-artist", "ai-multimodal", "antibridge",
    "bridge", "cc-cli-input-rules", "chrome-profile", "codebase-memory",
    "coding-level", "consulting", "content", "context-engineering",
    "cti-expert", "docs-seeker", "docx", "frontend-design", "generative_ui",
    "graphify", "markdown-novel-viewer", "migrate-workflows", "pdf",
    "pipeline", "plans-kanban", "pptx", "preview", "research", "scenario",
    "scout", "sequential-thinking", "show-off", "skill-creator", "stitch",
    "team", "tech-graph", "threejs", "ui-ux-pro-max", "use-mcp",
    "watzup", "worktree", "xlsx", "book-club-poster", "brain-evolution-log",
    "dispatch", "project-idea",
}


def extract_mekong_command(skill_path: Path) -> str | None:
    """Extract the mekong command invocation from a SKILL.md file.

    Looks for 'mekong <cmd> [args]' inside ```bash code blocks first,
    then falls back to any 'mekong <cmd>' pattern in the file.
    Returns the command portion (e.g., 'binh phap', 'mk ask', 'cook-auto').
    """
    content = skill_path.read_text(encoding="utf-8")

    # Strategy 1: find mekong invocations inside bash code blocks
    code_blocks = re.findall(r"```(?:bash|sh)\n(.*?)```", content, re.DOTALL)
    for block in code_blocks:
        match = re.search(r"mekong\s+(.+?)(?:\s+\$|\s*\n|\s*$)", block)
        if match:
            cmd = match.group(1).strip()
            # Remove quotes, trailing args
            cmd = cmd.replace('"', '').replace("'", '')
            # Stop at $ARGUMENTS or --
            cmd = re.split(r'\s+--\s|\s+\$', cmd)[0].strip()
            if cmd and not cmd.startswith("$") and not cmd.startswith("<"):
                return cmd

    # Strategy 2: fall back to inline mekong references
    matches = re.findall(r"mekong\s+([\w][\w\s-]*?)(?:\s+\$|\s+--|\s*\n|\s*$)", content)
    for m in matches:
        cmd = m.strip()
        if cmd and not cmd.startswith("$") and not cmd.startswith("<") \
                and cmd not in ("description:", "cli", "binary"):
            return cmd

    return None


def extract_description(skill_path: Path) -> str:
    """Extract the description from SKILL.md frontmatter."""
    content = skill_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    in_frontmatter = False
    desc_lines: list[str] = []
    collecting_desc = False

    for line in lines:
        if line.strip() == "---":
            if in_frontmatter:
                break
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line.startswith("description:"):
                desc_val = line[len("description:"):].strip()
                if desc_val and desc_val not in (">-", "|"):
                    # Inline description
                    if (desc_val.startswith('"') and desc_val.endswith('"')) or \
                       (desc_val.startswith("'") and desc_val.endswith("'")):
                        desc_val = desc_val[1:-1]
                    return desc_val
                collecting_desc = True
                continue
            if collecting_desc:
                stripped = line.strip()
                if stripped and not stripped.startswith("---"):
                    desc_lines.append(stripped)
                else:
                    break

    return " ".join(desc_lines).strip()


def probe_command(cmd: str) -> tuple[int, str]:
    """Probe a mekong command with --help, return (exit_code, category)."""
    mekong_bin = shutil.which("mekong")
    if not mekong_bin:
        return (-1, "no-binary")

    try:
        parts = cmd.split()
        result = subprocess.run(
            [mekong_bin] + parts + ["--help"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            if "COMMAND [ARGS]" in result.stdout or "Commands" in result.stdout:
                return (0, "sub-command-group")
            return (0, "executable")
        return (result.returncode, "error")
    except subprocess.TimeoutExpired:
        return (-2, "timeout")
    except Exception as e:
        return (-3, f"exception: {e}")


def audit_all_skills() -> list[dict]:
    """Audit every skill and return classification records."""
    records = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        name = skill_dir.name
        cmd = extract_mekong_command(skill_file)
        desc = extract_description(skill_file)

        is_generic = bool(re.match(
            r"^(Execute Mekong CLI .* workflow|Run Mekong .*workflow command)\.*$",
            desc,
        ))

        if name in ANTIGRAVITY_ONLY_SKILLS:
            category = "antigravity-only"
            exit_code = None
            probe_detail = "skipped — no CLI backend"
        else:
            # Try extracted command first, then derive from skill name
            commands_to_try = []
            if cmd:
                commands_to_try.append(cmd)
            # Derive command from skill name (e.g., mk-ask → mk ask, binh-phap → binh-phap)
            derived = name  # try skill name as-is first
            commands_to_try.append(derived)
            # For mk-* skills, also try 'mk <subcmd>'
            if name.startswith("mk-"):
                commands_to_try.append(f"mk {name[3:]}")

            category = "no-command-found"
            exit_code = None
            probe_detail = "no valid mekong command found"

            for try_cmd in commands_to_try:
                exit_code, probe_detail = probe_command(try_cmd)
                if exit_code == 0:
                    category = probe_detail  # "executable" or "sub-command-group"
                    cmd = try_cmd
                    break
            else:
                if exit_code is not None and exit_code != 0:
                    category = "antigravity-only"
                    probe_detail = f"no matching CLI command (skill is Antigravity-native)"

        records.append({
            "skill": name,
            "command": cmd,
            "category": category,
            "exit_code": exit_code,
            "probe_detail": probe_detail,
            "description": desc,
            "description_is_generic": is_generic,
        })

    return records


def main() -> None:
    print("Auditing all Antigravity skills...")
    records = audit_all_skills()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps({
            "schema": "mekong.antigravity.audit.v1",
            "total_skills": len(records),
            "categories": {
                "executable": sum(1 for r in records if r["category"] == "executable"),
                "sub-command-group": sum(1 for r in records if r["category"] == "sub-command-group"),
                "antigravity-only": sum(1 for r in records if r["category"] == "antigravity-only"),
                "probe-failed": sum(1 for r in records if r["category"] == "probe-failed"),
                "no-command-found": sum(1 for r in records if r["category"] == "no-command-found"),
            },
            "generic_descriptions": sum(1 for r in records if r["description_is_generic"]),
            "skills": records,
        }, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Audit complete: {len(records)} skills classified → {REPORT_PATH}")

    # Print summary
    cats = {}
    for r in records:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")

    generic = [r["skill"] for r in records if r["description_is_generic"]]
    if generic:
        print(f"\n⚠️  {len(generic)} skills with generic descriptions:")
        for s in generic:
            print(f"    - {s}")

    failed = [r for r in records if r["category"] == "probe-failed"]
    if failed:
        print(f"\n❌ {len(failed)} skills with probe failures:")
        for r in failed:
            print(f"    - {r['skill']}: {r['command']} → exit {r['exit_code']}")


if __name__ == "__main__":
    main()
