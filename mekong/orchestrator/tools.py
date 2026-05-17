"""Tool adapters — what the autopilot can DO inside its sandbox.

Every tool is invoked from the orchestrator parsing structured commands the
LLM emits inside <tool>...</tool> blocks. Each tool returns a `ToolResult`
that becomes the next user turn.

Allowed tools (and only these):
  READ <path>                  — read a repo file (lazy include)
  LS [path]                    — list a directory
  WRITE <path>                 - write/create file (multiline body follows on next turn)
  EDIT <path>                  - replace block (LLM emits <old>...</old><new>...</new>)
  BASH <command>               — run shell with safelist filter
  GIT <subcommand>             — git op (status, add, commit, …)
  TEST                         — run project test suite
  TYPECHECK                    — run npm run typecheck (dashboard) or mypy
  CHECKPOINT <message>         — claudekit checkpoint
  DONE <message>               — terminate loop with success
  ABORT <reason>               — terminate loop with failure
"""

from __future__ import annotations

import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Bash safelist — only commands that match are run unattended. Anything else
# requires explicit human override (`--unsafe-bash`).
SAFE_BASH_PREFIXES = (
    "ls", "cat", "head", "tail", "wc", "grep", "find", "sed -n",
    "echo", "pwd", "which",
    "python3 -c", "python3 -m pytest", "python3 -m mypy",
    "node --version", "node --check",
    "npm run", "npm test", "npx tsc",
    "pnpm run", "pnpm test",
    "git status", "git diff", "git log", "git show", "git ls-files",
    "make ", "bash scripts/",
    "ruff check", "black --check",
)


@dataclass
class ToolResult:
    ok: bool
    output: str
    truncated: bool = False


@dataclass
class ToolCall:
    tool: str
    args: str
    body: str = ""  # for WRITE / EDIT


_CMD_RE = re.compile(
    r"^\s*(READ|LS|WRITE|EDIT|BASH|GIT|TEST|TYPECHECK|CHECKPOINT|DONE|ABORT)\b\s*(.*)$",
    re.IGNORECASE,
)


def parse_tool_call(text: str) -> ToolCall | None:
    """Look for <tool>...</tool> block; parse first command."""
    m = re.search(r"<tool>\s*(.*?)\s*</tool>", text, re.DOTALL | re.IGNORECASE)
    if not m:
        return None
    block = m.group(1).strip()
    # First line is the command + args
    lines = block.splitlines()
    head = lines[0] if lines else ""
    body = "\n".join(lines[1:]).strip()
    cm = _CMD_RE.match(head)
    if not cm:
        return None
    return ToolCall(tool=cm.group(1).upper(), args=cm.group(2).strip(), body=body)


def is_bash_safe(cmd: str) -> bool:
    cmd = cmd.strip()
    return any(cmd.startswith(p) for p in SAFE_BASH_PREFIXES)


def _truncate(s: str, max_chars: int = 8_000) -> tuple[str, bool]:
    if len(s) <= max_chars:
        return s, False
    return s[: max_chars] + f"\n... [truncated at {max_chars} chars]", True


def run_bash(repo_root: Path, cmd: str, timeout: int = 60) -> ToolResult:
    if not is_bash_safe(cmd):
        return ToolResult(False, f"REJECTED unsafe bash: {cmd}")
    try:
        r = subprocess.run(
            cmd, shell=True, cwd=repo_root,
            capture_output=True, text=True, timeout=timeout,
        )
        out = (r.stdout or "") + (("\n--- STDERR ---\n" + r.stderr) if r.stderr else "")
        out, truncated = _truncate(out)
        ok = r.returncode == 0
        if not ok:
            out = f"exit={r.returncode}\n{out}"
        return ToolResult(ok, out, truncated)
    except subprocess.TimeoutExpired:
        return ToolResult(False, f"TIMEOUT after {timeout}s: {cmd}")


def run_git(repo_root: Path, args: str) -> ToolResult:
    return run_bash(repo_root, f"git {args}", timeout=30)


def write_file(repo_root: Path, rel_path: str, body: str) -> ToolResult:
    full = (repo_root / rel_path).resolve()
    if not str(full).startswith(str(repo_root.resolve())):
        return ToolResult(False, f"REJECTED: path escapes repo: {rel_path}")
    # Refuse to write into PUBLIC_BOUNDARY paths (per CLAUDE.md)
    forbidden = ("apps/", "mekong/daemon/", ".env", ".env.")
    rel_str = str(rel_path).lstrip("./")
    if any(rel_str.startswith(p) for p in forbidden) and rel_str not in ("apps/dashboard/.env.local.example",):
        return ToolResult(False, f"REJECTED: writes to {rel_path} are blocked by CLAUDE.md public-repo boundary. Use --override-boundary if absolutely intentional.")
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(body, encoding="utf-8")
    return ToolResult(True, f"wrote {len(body)} chars to {rel_path}")


def edit_file(repo_root: Path, rel_path: str, body: str) -> ToolResult:
    """Body must contain <old>...</old><new>...</new>."""
    full = (repo_root / rel_path).resolve()
    if not str(full).startswith(str(repo_root.resolve())) or not full.is_file():
        return ToolResult(False, f"REJECTED edit (path or file): {rel_path}")
    om = re.search(r"<old>(.*?)</old>", body, re.DOTALL)
    nm = re.search(r"<new>(.*?)</new>", body, re.DOTALL)
    if not om or not nm:
        return ToolResult(False, "EDIT body must include <old>...</old><new>...</new>")
    text = full.read_text(encoding="utf-8")
    old, new = om.group(1), nm.group(1)
    if old not in text:
        return ToolResult(False, f"<old> block not found in {rel_path}")
    if text.count(old) > 1:
        return ToolResult(False, f"<old> block matches {text.count(old)}× in {rel_path} — make it more specific")
    full.write_text(text.replace(old, new, 1), encoding="utf-8")
    return ToolResult(True, f"edited {rel_path} (1 replacement)")


def run_test(repo_root: Path) -> ToolResult:
    if (repo_root / "pytest.ini").exists() or (repo_root / "pyproject.toml").exists():
        return run_bash(repo_root, "python3 -m pytest -x --tb=short", timeout=300)
    if (repo_root / "package.json").exists():
        return run_bash(repo_root, "npm test --silent", timeout=300)
    return ToolResult(False, "no test runner detected")


def run_typecheck(repo_root: Path) -> ToolResult:
    if (repo_root / "apps/dashboard/tsconfig.json").exists():
        return run_bash(repo_root, "cd apps/dashboard && npm run typecheck", timeout=120)
    if (repo_root / "pyproject.toml").exists():
        return run_bash(repo_root, "python3 -m mypy --ignore-missing-imports src/", timeout=120)
    return ToolResult(False, "no typecheck configured")


def run_checkpoint(repo_root: Path, message: str) -> ToolResult:
    """claudekit checkpoint, fall back to git stash if not installed."""
    cmd = f"npx --yes claudekit checkpoint create {shlex.quote(message)}"
    r = subprocess.run(cmd, shell=True, cwd=repo_root, capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        return ToolResult(True, f"claudekit checkpoint: {message}")
    # fallback
    return run_bash(repo_root, f'git add -A && git commit -m "checkpoint: {message}" --allow-empty')
