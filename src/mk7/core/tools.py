"""Mekong CLI 7 — Tool whitelist + executor (port of opencode tools).

Whitelisted tools for graph nodes: read, write, cat, bash(-test), grep,
glob, edit, apply_patch, webfetch, question.
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

from .gates import GateNotAllowed, SAFE_TOOLS

# Commands that must NEVER run through bash-test (destructive / irreversible).
FORBIDDEN_SHELL = (
    "rm ",
    "rm -",
    "mv ",
    "shutil.rmtree",
    "os.remove",
    "git push",
    "git reset --hard",
    "sudo ",
    "mkfs",
    "dd ",
    "> /dev/sd",
)

TOOL_TIMEOUT = 60
FETCH_TIMEOUT = 20
MAX_QUESTION_OPTIONS = 6


class ToolError(RuntimeError):
    pass


def ensure_tool_allowed(command: str) -> None:
    base = command.strip().split(" ")[0].lower()
    if base not in SAFE_TOOLS:
        raise GateNotAllowed(f"tool '{base}' is not in whitelist {sorted(SAFE_TOOLS)}")


def ensure_shell_safe(command: str) -> None:
    lowered = command.lower()
    for forbidden in FORBIDDEN_SHELL:
        if forbidden in lowered:
            raise GateNotAllowed(f"shell command contains forbidden pattern: {forbidden.strip()}")


def run_tool(command: str, cwd: str | None = None, timeout: int = TOOL_TIMEOUT) -> dict[str, Any]:
    """Execute a whitelisted tool command, returning structured result.

    Returns {"tool": ..., "ok": bool, "output": str, "error": str}.
    """
    command = command.strip()
    if not command:
        raise ToolError("empty command")
    ensure_tool_allowed(command)
    base = command.split(" ")[0].lower()

    try:
        if base == "write":
            # write <path> --content <text> | write <path> <<<text
            parts = command.split(" ", 1)
            if len(parts) < 2:
                raise ToolError("usage: write <path> <content>")
            rest = parts[1]
            if rest.startswith(("-c ", "--content ")):
                rest = rest[len("-c " if rest.startswith("-c ") else "--content ") :]
            path_str, _, content = rest.partition(" ")
            if not content:
                raise ToolError("usage: write <path> <content>")
            target = Path(path_str)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            return {"tool": "write", "ok": True, "output": f"wrote {path_str} ({len(content)} bytes)"}
        if base == "cat":
            parts = command.split(" ", 1)
            path_str = parts[1].strip() if len(parts) > 1 else ""
            if not path_str:
                raise ToolError("usage: cat <path>")
            return {"tool": "cat", "ok": True, "output": Path(path_str).read_text()[:2000]}
        if base == "read":
            parts = command.split(" ", 1)
            path_str = parts[1].strip() if len(parts) > 1 else ""
            if not path_str:
                raise ToolError("usage: read <path>")
            return {"tool": "read", "ok": True, "output": Path(path_str).read_text()[:4000]}
        if base == "bash-test":
            body = command.split(" ", 1)[1] if " " in command else ""
            ensure_shell_safe(body)
            proc = subprocess.run(body, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd)
            return {
                "tool": "bash-test",
                "ok": proc.returncode == 0,
                "output": (proc.stdout + proc.stderr).strip()[:2000],
                "error": "" if proc.returncode == 0 else f"exit {proc.returncode}",
            }
        if base == "bash":
            body = command.split(" ", 1)[1] if " " in command else ""
            ensure_shell_safe(body)
            proc = subprocess.run(body, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd)
            return {
                "tool": "bash",
                "ok": proc.returncode == 0,
                "output": (proc.stdout + proc.stderr).strip()[:2000],
                "error": "" if proc.returncode == 0 else f"exit {proc.returncode}",
            }
        if base == "grep":
            # grep <regex> [path] [--include ext]
            parts = command.split(" ", 2)
            pattern = parts[1] if len(parts) > 1 else ""
            if not pattern:
                raise ToolError("usage: grep <regex> [path]")
            search_path = parts[2] if len(parts) > 2 else "."
            proc = subprocess.run(
                ["rg", "--line-number", "--no-heading", "--color", "never", pattern, search_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            output = (proc.stdout or "").strip()
            return {
                "tool": "grep",
                "ok": proc.returncode in (0, 1),
                "output": output[:2000] or "(no matches)",
                "error": "" if proc.returncode in (0, 1) else proc.stderr[:300],
            }
        if base == "glob":
            # glob <pattern>
            parts = command.split(" ", 1)
            pattern = parts[1].strip() if len(parts) > 1 else ""
            if not pattern:
                raise ToolError("usage: glob <pattern>")
            from glob import glob as _glob

            hits = sorted(_glob(pattern, recursive=True, include_hidden=False))
            return {"tool": "glob", "ok": True, "output": "\n".join(hits[:200]) or "(no files)"}
        if base == "edit":
            # edit <path> --old <text> --new <text>
            m = re.match(r"edit\s+(\S+)\s+--old\s+(.*?)\s+--new\s+(.*)$", command, re.DOTALL)
            if not m:
                raise ToolError('usage: edit <path> --old <text> --new <text>')
            path_str, old, new = m.group(1), m.group(2), m.group(3)
            target = Path(path_str)
            text = target.read_text()
            if old not in text:
                return {"tool": "edit", "ok": False, "output": "", "error": f"old text not found in {path_str}"}
            target.write_text(text.replace(old, new, 1))
            return {"tool": "edit", "ok": True, "output": f"edited {path_str}"}
        if base == "apply-patch" or base == "apply_patch":
            # apply_patch <patch text with *** markers>
            body = command.split(" ", 1)[1] if " " in command else ""
            if "*** Add File:" not in body and "*** Update File:" not in body:
                raise ToolError("usage: apply_patch <patch with *** Add/Update File: markers>")
            applied = _apply_patch_body(body)
            return {"tool": "apply_patch", "ok": True, "output": applied}
        if base == "webfetch":
            url = command.split(" ", 1)[1].strip() if " " in command else ""
            if not url.startswith(("http://", "https://")):
                raise ToolError("usage: webfetch <url>")
            req = urllib.request.Request(url, headers={"User-Agent": "mekong-cli/7"})
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
                data = resp.read(100_000).decode(errors="replace")
            # crude markdown-ish: strip tags
            text = re.sub(r"<script[\s\S]*?</script>", " ", data, flags=re.I)
            text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s{2,}", " ", text).strip()
            return {"tool": "webfetch", "ok": True, "output": text[:3000]}
        if base == "question":
            # question <question text> [options...] — interactive via stdin
            body = command.split(" ", 1)[1] if " " in command else ""
            if not body:
                raise ToolError("usage: question <question>")
            lines = body.split("\n")
            q = lines[0].strip()
            options = [ln.strip() for ln in lines[1:] if ln.strip()][:MAX_QUESTION_OPTIONS]
            answer = _ask_question(q, options)
            return {"tool": "question", "ok": True, "output": f"operator answer: {answer}"}
        if base == "lsp":
            # lsp <symbol> [def|refs] [search_dir]
            parts = command.split(" ")
            symbol = parts[1] if len(parts) > 1 else ""
            if not symbol:
                raise ToolError("usage: lsp <symbol> [def|refs] [dir]")
            op = parts[2] if len(parts) > 2 else "def"
            search_dir = parts[3] if len(parts) > 3 else "."
            from .lsp import find_references, go_to_definition

            hits = go_to_definition(symbol, search_dir) if op in ("def", "definition") else find_references(symbol, search_dir)
            if not hits:
                return {"tool": "lsp", "ok": True, "output": f"(no {op} found for {symbol})"}
            lines = [f"{h['path']}:{h['line']}: {h.get('text', '')[:100]}" for h in hits[:20]]
            return {"tool": "lsp", "ok": True, "output": "\n".join(lines)}
        raise ToolError(f"unsupported tool '{base}'")
    except GateNotAllowed:
        raise
    except ToolError:
        raise
    except Exception as e:
        return {"tool": base, "ok": False, "output": "", "error": str(e)[:300]}


def _apply_patch_body(body: str) -> str:
    """Apply opencode-style *** Add/Update File: markers. Returns summary."""
    applied: list[str] = []
    current_file: Path | None = None
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m_add = re.match(r"\*\*\* Add File:\s*(.+)", line)
        m_upd = re.match(r"\*\*\* Update File:\s*(.+)", line)
        m_del = re.match(r"\*\*\* Delete File:\s*(.+)", line)
        m_move = re.match(r"\*\*\* Move to:\s*(.+)", line)
        if m_add:
            current_file = Path(m_add.group(1).strip())
            current_file.parent.mkdir(parents=True, exist_ok=True)
            content: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("*** "):
                content.append(lines[i])
                i += 1
            current_file.write_text("\n".join(content).rstrip("\n") + "\n")
            applied.append(f"added {current_file}")
            continue
        if m_upd:
            current_file = Path(m_upd.group(1).strip())
            old_lines: list[str] = []
            new_lines: list[str] = []
            i += 1
            # read until "---" separator
            while i < len(lines) and lines[i].strip() != "---":
                old_lines.append(lines[i])
                i += 1
            i += 1  # skip ---
            while i < len(lines) and not lines[i].startswith("*** "):
                new_lines.append(lines[i])
                i += 1
            old_block = "\n".join(old_lines).strip()
            new_block = "\n".join(new_lines).strip()
            text = current_file.read_text()
            if not old_block:
                # append mode (no old block provided)
                current_file.write_text(text.rstrip("\n") + "\n" + new_block + "\n")
                applied.append(f"appended {current_file}")
            elif old_block in text:
                text = text.replace(old_block, new_block, 1)
                current_file.write_text(text)
                applied.append(f"updated {current_file}")
            else:
                applied.append(f"skip {current_file} (old block not found)")
            continue
        if m_del:
            path = Path(m_del.group(1).strip())
            if path.exists():
                path.unlink()
                applied.append(f"deleted {path}")
            i += 1
            continue
        if m_move:
            applied.append(f"move marker ignored: {m_move.group(1)}")
            i += 1
            continue
        i += 1
    return "; ".join(applied) if applied else "no changes applied"


def _ask_question(question: str, options: list[str]) -> str:
    """Ask the operator a question (question tool, interactive)."""
    print(f"\n? {question}")
    if options:
        for idx, opt in enumerate(options, 1):
            print(f"  {idx}. {opt}")
        try:
            choice = input("> ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return options[int(choice) - 1]
            return choice
        except EOFError:
            return "aborted (EOF)"
    try:
        return input("> ").strip() or "aborted (empty)"
    except EOFError:
        return "aborted (EOF)"
