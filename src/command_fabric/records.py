# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Command fabric record model and source-file parsing."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandRecord:
    """Portable command record used by CLI, IDE, SDK, and MCP adapters."""

    name: str
    source: str
    description: str
    argument_hint: str
    allowed_tools: list[str]
    execution: str
    contract: str | None
    layer: str | None
    portability_targets: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable command record."""
        return asdict(self)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse simple YAML-like frontmatter used by command markdown files."""
    if not text.startswith("---\n"):
        return {}, text

    end = text.find("\n---", 4)
    if end == -1:
        return {}, text

    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip()
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields, body


def _is_directory_tree_or_diagram(text: str) -> bool:
    """Check if code block is a directory tree or ASCII diagram rather than a command."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return True
    tree_chars = ("├──", "└──", "│", "├─", "└─", "|--", "`--")
    if any(any(tc in line for tc in tree_chars) for line in lines):
        return True
    file_pattern = re.compile(r"^[.\w/\\-]+\.[a-zA-Z0-9]+(?:\s*#.*)?$")
    if all(file_pattern.match(line) for line in lines):
        return True
    return False


def extract_execution(body: str) -> str:
    """Extract executable command from command markdown.

    Only extracts valid executable shell/CLI blocks (or explicit ## Execution
    bash/sh blocks), never unlabelled directory tree blocks or ASCII diagrams.
    """
    exec_section_match = re.search(
        r"##\s+Execution\b(.*?)(?=\n##\s+|\Z)", body, re.DOTALL | re.IGNORECASE
    )
    if exec_section_match:
        section_text = exec_section_match.group(1)
        for match in re.finditer(
            r"```(?:bash|sh|zsh)?\n(?P<command>.*?)\n```", section_text, re.DOTALL
        ):
            candidate = match.group("command").strip()
            if candidate and not _is_directory_tree_or_diagram(candidate):
                return candidate

    for match in re.finditer(
        r"```(?:bash|sh|zsh)\n(?P<command>.*?)\n```", body, re.DOTALL
    ):
        candidate = match.group("command").strip()
        if candidate and not _is_directory_tree_or_diagram(candidate):
            return candidate

    return ""


def split_allowed_tools(value: str) -> list[str]:
    """Split allowed-tools frontmatter into normalized tool names."""
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def contract_layer(contract_path: Path) -> str | None:
    """Read optional command layer from factory contract JSON."""
    if not contract_path.exists():
        return None
    try:
        data = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    layer = data.get("layer")
    return str(layer) if layer else None


def _canonical_source_path(path: Path, root: Path) -> Path:
    """Map the integration command fallback to the canonical `.claude/commands/` root."""
    integration_dir = root / ".claude" / "_integration" / "commands"
    try:
        return root / ".claude" / "commands" / path.relative_to(integration_dir)
    except ValueError:
        return path


def display_source(path: Path, root: Path) -> str:
    """Return a stable source path for project and user command roots."""
    path = _canonical_source_path(path, root)
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        pass
    try:
        return "~/" + path.relative_to(Path.home()).as_posix()
    except ValueError:
        return path.as_posix()


def portability_targets(record_name: str, execution: str) -> list[str]:
    """Infer adapter targets from a command record."""
    targets = ["mekong-cli", "claude-code", "codex", "gemini-cli", "opencode", "kiro-cli", "mcp"]
    if execution.startswith("python3 -m src.main") or execution.startswith("mekong "):
        targets.extend([
            "shell", "vscode", "cursor", "windsurf", "theia", "jetbrains",
            "visual-studio", "eclipse", "fleet", "nova", "lapce", "kakoune",
            "micro", "vim", "neovim", "helix", "zed", "emacs", "sublime",
        ])
    if record_name.startswith("mk-"):
        targets.append("mk-wrapper")
    return sorted(set(targets))


def command_record_from_markdown(path: Path, root: Path, contracts_dir: Path) -> CommandRecord:
    """Create a command record from one `.claude/commands/*.md` file."""
    frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    name = path.stem
    execution = extract_execution(body)
    contract_path = contracts_dir / f"{name}.json"
    contract_rel = contract_path.relative_to(root).as_posix() if contract_path.exists() else None
    return CommandRecord(
        name=name, source=display_source(path, root),
        description=frontmatter.get("description", ""),
        argument_hint=frontmatter.get("argument-hint", ""),
        allowed_tools=split_allowed_tools(frontmatter.get("allowed-tools", "")),
        execution=execution, contract=contract_rel,
        layer=contract_layer(contract_path),
        portability_targets=portability_targets(name, execution),
    )


__all__ = [
    "CommandRecord", "command_record_from_markdown", "contract_layer", "display_source",
    "extract_execution", "parse_frontmatter", "portability_targets", "split_allowed_tools",
]
