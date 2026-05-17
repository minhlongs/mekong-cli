"""Context manager — keeps a 1M-token conversation healthy.

Strategy:
- Index the repo on start (paths + 1-line summaries) → ~10k tokens.
- Lazily include full file content when the LLM asks for it (`READ <path>`).
- Track which files are already in context; never re-include.
- When `tokens_used > compact_threshold`, ask the LLM to summarize
  the OLD turns and replace them in-place.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Turn:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tag: str = ""  # optional label: "plan", "execute", "verify"


@dataclass
class ContextManager:
    repo_root: Path
    compact_threshold: int = 600_000
    skip_dirs: tuple[str, ...] = (
        "node_modules", ".git", ".venv", ".venv-seed", "target", ".turbo",
        "__pycache__", ".next", "dist", "build", "coverage",
    )
    skip_exts: tuple[str, ...] = (
        ".lock", ".log", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf",
        ".zip", ".tar", ".gz", ".woff", ".woff2", ".ttf", ".otf",
        ".dylib", ".so", ".rlib", ".rmeta", ".pyc",
    )
    max_file_chars: int = 60_000  # ~15k tokens, refuse to include huge files

    turns: list[Turn] = field(default_factory=list)
    included_files: set[str] = field(default_factory=set)
    repo_index: list[str] = field(default_factory=list)

    def index_repo(self) -> str:
        """Walk repo, build a path index. Cheap — only paths, not content."""
        self.repo_index.clear()
        for p in self.repo_root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(self.repo_root)
            parts = rel.parts
            if any(d in parts for d in self.skip_dirs):
                continue
            if p.suffix.lower() in self.skip_exts:
                continue
            try:
                size = p.stat().st_size
            except OSError:
                continue
            if size > self.max_file_chars:
                continue
            self.repo_index.append(f"{rel}\t{size}")
        return f"Repo index: {len(self.repo_index)} files\n" + "\n".join(self.repo_index[:2000])

    def add(self, role: str, content: str, tag: str = "") -> None:
        self.turns.append(Turn(role=role, content=content, tag=tag))

    def read_file(self, rel_path: str) -> str:
        """Read a file by repo-relative path. Refuses outside repo or huge files."""
        if rel_path in self.included_files:
            return f"(already in context: {rel_path})"
        full = (self.repo_root / rel_path).resolve()
        if not str(full).startswith(str(self.repo_root.resolve())):
            return f"ERROR: path escapes repo root: {rel_path}"
        if not full.is_file():
            return f"ERROR: not a file: {rel_path}"
        try:
            text = full.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"ERROR reading {rel_path}: {e}"
        if len(text) > self.max_file_chars:
            text = text[: self.max_file_chars] + f"\n... [truncated at {self.max_file_chars} chars]"
        self.included_files.add(rel_path)
        return text

    def messages(self) -> list[dict[str, str]]:
        """Materialise turns as OpenAI-compat messages."""
        return [{"role": t.role, "content": t.content} for t in self.turns]

    def estimate_tokens(self) -> int:
        """Rough estimate — 4 chars ≈ 1 token."""
        total = sum(len(t.content) for t in self.turns)
        return total // 4

    def needs_compact(self) -> bool:
        return self.estimate_tokens() > self.compact_threshold

    def compact(self, summary: str) -> None:
        """Replace all but the last 4 turns with a single summary turn."""
        if len(self.turns) <= 4:
            return
        head = self.turns[0] if self.turns and self.turns[0].role == "system" else None
        tail = self.turns[-4:]
        new_turns: list[Turn] = []
        if head and head not in tail:
            new_turns.append(head)
        new_turns.append(Turn(role="user", content=f"[CONTEXT COMPACTED]\n{summary}", tag="compact"))
        new_turns.extend(tail)
        self.turns = new_turns

    def dump(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "repo_root": str(self.repo_root),
            "included_files": sorted(self.included_files),
            "turns": [{"role": t.role, "tag": t.tag, "content": t.content} for t in self.turns],
            "estimate_tokens": self.estimate_tokens(),
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
