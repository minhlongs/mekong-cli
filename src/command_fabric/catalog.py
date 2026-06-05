"""Neutral command catalog for global IDE/CLI adapters.

The command fabric reads existing command source files instead of duplicating
their definitions. Adapters can export this catalog to shells, IDEs, MCP, SDKs,
and agent runtimes without maintaining separate command lists.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMMANDS_DIR = PROJECT_ROOT / ".claude" / "commands"
DEFAULT_USER_COMMANDS_DIR = Path.home() / ".claude" / "commands"
DEFAULT_CONTRACTS_DIR = PROJECT_ROOT / "factory" / "contracts" / "commands"


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


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
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


def _extract_execution(body: str) -> str:
    """Extract the first fenced execution command from command markdown."""
    match = re.search(r"```(?:bash|sh)?\n(?P<command>.*?)\n```", body, re.DOTALL)
    if not match:
        return ""
    return match.group("command").strip()


def _split_allowed_tools(value: str) -> list[str]:
    """Split allowed-tools frontmatter into normalized tool names."""
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _contract_layer(contract_path: Path) -> str | None:
    """Read optional command layer from factory contract JSON."""
    if not contract_path.exists():
        return None
    try:
        data = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    layer = data.get("layer")
    return str(layer) if layer else None


def _display_source(path: Path, root: Path) -> str:
    """Return a stable source path for project and user command roots."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        pass

    home = Path.home()
    try:
        return "~/" + path.relative_to(home).as_posix()
    except ValueError:
        return path.as_posix()


def _portability_targets(record_name: str, execution: str) -> list[str]:
    """Infer adapter targets from a command record."""
    targets = ["mekong-cli", "claude-code", "codex", "gemini-cli", "opencode", "mcp"]
    if execution.startswith("python3 -m src.main") or execution.startswith("mekong "):
        targets.extend(["shell", "vscode", "cursor", "jetbrains"])
    if record_name.startswith("mk-"):
        targets.append("mk-wrapper")
    return sorted(set(targets))


def command_record_from_markdown(path: Path, root: Path = PROJECT_ROOT) -> CommandRecord:
    """Create a command record from one `.claude/commands/*.md` file."""
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(text)
    name = path.stem
    execution = _extract_execution(body)
    contract_path = DEFAULT_CONTRACTS_DIR / f"{name}.json"
    contract_rel = contract_path.relative_to(root).as_posix() if contract_path.exists() else None

    return CommandRecord(
        name=name,
        source=_display_source(path, root),
        description=frontmatter.get("description", ""),
        argument_hint=frontmatter.get("argument-hint", ""),
        allowed_tools=_split_allowed_tools(frontmatter.get("allowed-tools", "")),
        execution=execution,
        contract=contract_rel,
        layer=_contract_layer(contract_path),
        portability_targets=_portability_targets(name, execution),
    )


def build_command_catalog(
    commands_dir: Path = DEFAULT_COMMANDS_DIR,
    root: Path = PROJECT_ROOT,
) -> list[CommandRecord]:
    """Build the sorted command fabric catalog from source command files."""
    records = [
        command_record_from_markdown(path, root=root)
        for path in sorted(commands_dir.glob("*.md"))
        if path.is_file()
    ]
    return sorted(records, key=lambda record: record.name)


def _readable_command_records(commands_dir: Path, root: Path) -> list[CommandRecord]:
    """Return readable command records from one command directory."""
    if not commands_dir.exists():
        return []

    records: list[CommandRecord] = []
    for path in sorted(commands_dir.glob("*.md")):
        try:
            records.append(command_record_from_markdown(path, root=root))
        except OSError:
            continue
        except UnicodeDecodeError:
            continue
    return records


def build_global_command_catalog(
    commands_dirs: Sequence[Path] | None = None,
    root: Path = PROJECT_ROOT,
) -> list[CommandRecord]:
    """Build a merged project + user command catalog for non-slash runtimes.

    Project commands win name conflicts so `mekong` behavior remains canonical,
    while user-level ClaudeKit commands are still visible to wrappers, APIs,
    IDEs, and agent CLIs that cannot rely on Claude Code's slash-command UI.
    """
    dirs = list(commands_dirs) if commands_dirs is not None else [
        DEFAULT_COMMANDS_DIR,
        DEFAULT_USER_COMMANDS_DIR,
    ]
    by_name: dict[str, CommandRecord] = {}
    for commands_dir in dirs:
        for record in _readable_command_records(commands_dir, root):
            by_name.setdefault(record.name, record)
    return sorted(by_name.values(), key=lambda record: record.name)


def export_command_catalog(
    records: list[CommandRecord] | None = None,
    source: str = ".claude/commands + ~/.claude/commands",
) -> dict[str, Any]:
    """Export command catalog as a stable machine-readable payload."""
    command_records = records if records is not None else build_global_command_catalog()
    return {
        "schema": "mekong.command_fabric.v1",
        "version": "2026.06.03",
        "source": source,
        "count": len(command_records),
        "commands": [record.to_dict() for record in command_records],
    }


__all__ = [
    "CommandRecord",
    "build_command_catalog",
    "build_global_command_catalog",
    "command_record_from_markdown",
    "export_command_catalog",
]
