"""Mekong CLI 7 — Minimal LSP-like code intelligence (port of opencode lsp tool).

Full LSP servers are heavy; this implements the two highest-value operations
(goToDefinition, findReferences) with ripgrep-based symbol resolution plus an
optional real LSP server adapter when one is configured.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any

LSP_TIMEOUT = 15


class LspError(RuntimeError):
    pass


@dataclass
class LspServer:
    name: str
    command: list[str]
    languages: list[str] = None  # type: ignore[assignment]


# ── ripgrep-based symbol resolution ─────────────────────────

_SYMBOL_PATTERNS = {
    "python": r"^(?:def|class|async def)\s+({name})\b",
    "typescript": r"^(?:export\s+)?(?:function|class|interface|type|const|let|var)\s+({name})\b",
    "javascript": r"^(?:export\s+)?(?:function|class|const|let|var)\s+({name})\b",
    "go": r"^(?:func|type|var|const)\s+({name})\b",
    "rust": r"^(?:fn|struct|enum|trait|impl|type|const)\s+({name})\b",
    "java": r"^(?:public|private|protected)?\s*(?:class|interface|enum|record)\s+({name})\b",
}


def _detect_language(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {
        "py": "python",
        "ts": "typescript",
        "tsx": "typescript",
        "js": "javascript",
        "jsx": "javascript",
        "go": "go",
        "rs": "rust",
        "java": "java",
    }.get(ext, "")


def _rg(pattern: str, search_dir: str, limit: int = 50) -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["rg", "--line-number", "--no-heading", "--color", "never", pattern, search_dir],
        capture_output=True,
        text=True,
        timeout=LSP_TIMEOUT,
    )
    hits: list[dict[str, Any]] = []
    for line in (proc.stdout or "").splitlines()[:limit]:
        parts = line.split(":", 2)
        if len(parts) >= 2:
            hits.append({"path": parts[0], "line": int(parts[1]), "text": parts[2] if len(parts) > 2 else ""})
    return hits


def go_to_definition(symbol: str, search_dir: str) -> list[dict[str, Any]]:
    """Find definition lines (best-effort via language patterns + fallback)."""
    pattern = None
    for lang, template in _SYMBOL_PATTERNS.items():
        p = template.format(name=re.escape(symbol))
        hits = _rg(p, search_dir, limit=5)
        if hits:
            pattern = p
            break
    if hits:  # type: ignore[possibly-undefined]
        return hits
    # Fallback: plain word search, prefer lines starting with the symbol.
    return _rg(rf"^\s*{re.escape(symbol)}\b", search_dir, limit=5)


def find_references(symbol: str, search_dir: str) -> list[dict[str, Any]]:
    return _rg(rf"\b{re.escape(symbol)}\b", search_dir, limit=50)


# ── Real LSP adapter (optional) ─────────────────────────────

class RealLspClient:
    """Minimal JSON-RPC LSP client (initialize/definition/references).

    Protocol version 3.17. Only supports a single document at a time.
    """

    def __init__(self, server: LspServer, root_uri: str, document_uri: str):
        self.server = server
        self.root_uri = root_uri
        self.document_uri = document_uri
        self._proc: subprocess.Popen | None = None
        self._req_id = 0
        self.initialized = False

    def _ensure(self) -> subprocess.Popen:
        if self._proc is None or self._proc.poll() is not None:
            self._proc = subprocess.Popen(
                self.server.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
            )
        return self._proc

    def _send(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        import select

        proc = self._ensure()
        self._req_id += 1
        assert proc.stdin and proc.stdout
        proc.stdin.write(
            json.dumps({"jsonrpc": "2.0", "id": self._req_id, "method": method, "params": params}) + "\n"
        )
        proc.stdin.flush()
        if not select.select([proc.stdout], [], [], LSP_TIMEOUT)[0]:
            raise LspError("LSP timeout")
        line = proc.stdout.readline()
        if not line:
            raise LspError("LSP closed")
        msg = json.loads(line)
        if "error" in msg and msg["error"]:
            raise LspError(f"LSP error: {msg['error']}")
        return msg.get("result", {})

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        proc = self._ensure()
        assert proc.stdin
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
        proc.stdin.flush()

    def initialize(self) -> None:
        self._send("initialize", {
            "processId": None,
            "rootUri": self.root_uri,
            "capabilities": {},
        })
        self._notify("initialized", {})
        self.initialized = True

    def definition(self, line: int, character: int, text: str) -> dict[str, Any]:
        if not self.initialized:
            self.initialize()
        self._notify("textDocument/didOpen", {
            "textDocument": {"uri": self.document_uri, "languageId": "python", "version": 1, "text": text},
        })
        result = self._send("textDocument/definition", {
            "textDocument": {"uri": self.document_uri},
            "position": {"line": line, "character": character},
        })
        return result

    def close(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                self._proc.kill()
        self._proc = None
