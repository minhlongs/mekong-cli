"""IdeaLoop — autonomous Plan → Execute → Verify → Reflect cycle.

Owns one run. Reads idea, plans tasks, generates code via LLM, runs tests,
reflects on failures, iterates until the LLM emits DONE or safety budget
is exhausted. Persists everything to `.mekong/idea/<run-id>/`.

Designed to be called from CLI (`mekong idea ...`) or from claudekit-driven
slash command. Uses Mekong's universal LLM client (auto-detects DeepSeek
local via Ollama / DeepSeek cloud / any OpenAI-compat endpoint).
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .context_manager import ContextManager
from .safety import SafetyBudget
from .tools import (
    ToolCall, ToolResult, edit_file, parse_tool_call,
    run_bash, run_checkpoint, run_git, run_test, run_typecheck, write_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class RunOptions:
    idea: str
    project: str = "default"
    worktree: bool = True
    max_iter: int = 12
    max_tokens: int = 800_000
    max_mcu: int = 50
    deploy: bool = False           # final step runs deploy script if green
    dry_run: bool = False          # emit plan only, no writes
    model: str | None = None       # override LLM_MODEL just for this run
    temperature: float = 0.4
    unsafe_bash: bool = False      # allow bash outside safelist
    override_boundary: bool = False


@dataclass
class RunResult:
    run_id: str
    ok: bool
    reason: str
    iterations: int
    files_touched: list[str]
    last_verify: str = ""
    audit_log: Path = field(default_factory=Path)


SYSTEM_PROMPT = """You are Mekong /idea autopilot — an autonomous senior engineer.

You have a 1M-token context window (DeepSeek). You drive a Plan → Execute → Verify → Reflect loop until the user's idea ships.

OUTPUT PROTOCOL — every turn you respond with EXACTLY one of:

1. A tool call wrapped in <tool>...</tool>:
   READ <path>                 — read repo file
   LS <path>                   — list directory
   WRITE <path>                — create/overwrite a file (body on next lines)
   EDIT <path>                 — surgical replace (<old>…</old><new>…</new>)
   BASH <cmd>                  — run safelisted shell command
   GIT <subcommand>            — git op (status/add/commit/log/diff)
   TEST                        — run project test suite
   TYPECHECK                   — run typecheck
   CHECKPOINT <msg>            — claudekit checkpoint (call after every successful Execute step)
   DONE <summary>              — terminate with success
   ABORT <reason>              — terminate with failure

2. A plain `<thinking>…</thinking>` block (does NOT count as a turn for verify, but use sparingly).

NEVER write prose outside these blocks. Never ask the user a question — you're autonomous. Make decisions.

CONSTRAINTS
- Refuse to write to `apps/` (private customer apps), `mekong/daemon/`, or any `.env*` file.
- Always CHECKPOINT before risky changes.
- Run TEST + TYPECHECK before DONE.
- If a tool returns ERROR three turns in a row on the same target, switch tactics or ABORT.
- Stay focused on the idea. Don't yak-shave.

THE WORKFLOW (default cadence)
1. PLAN  — break the idea into ≤6 tasks. WRITE the plan to `.mekong/idea/<run>/plan.md`.
2. For each task:
   a. READ relevant files
   b. WRITE / EDIT
   c. TYPECHECK
   d. TEST (if tests touched)
   e. CHECKPOINT
3. When all tasks complete + tests green → DONE.
"""


class IdeaLoop:
    def __init__(self, opts: RunOptions) -> None:
        self.opts = opts
        self.run_id = time.strftime("%y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        self.run_dir = REPO_ROOT / ".mekong" / "idea" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.audit_path = self.run_dir / "audit.jsonl"
        self.ctx = ContextManager(repo_root=REPO_ROOT)
        self.safety = SafetyBudget(
            max_iter=opts.max_iter,
            max_tokens=opts.max_tokens,
            max_mcu=opts.max_mcu,
            state_file=self.run_dir / "safety.json",
        )
        self.safety.install_signal_handlers()
        self.files_touched: set[str] = set()
        self._client = None  # lazy

    def _llm(self):  # type: ignore[no-untyped-def]
        if self._client is None:
            try:
                from core.llm_client import get_client  # type: ignore
            except ImportError:
                from src.core.llm_client import get_client  # type: ignore
            self._client = get_client()
        return self._client

    def _audit(self, kind: str, payload: Any) -> None:
        rec = {"t": time.time(), "kind": kind, "payload": payload}
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    def _llm_turn(self) -> str:
        kw: dict[str, Any] = {"temperature": self.opts.temperature}
        if self.opts.model:
            kw["model"] = self.opts.model
        client = self._llm()
        resp = client.chat(self.ctx.messages(), **kw)
        content = getattr(resp, "content", str(resp))
        self.ctx.add("assistant", content)
        # rough token accounting
        self.safety.record_tokens(self.ctx.estimate_tokens())
        self.safety.record_mcu(1)
        self._audit("llm", {"chars": len(content)})
        return content

    def _dispatch(self, call: ToolCall) -> tuple[ToolResult, bool]:
        """Return (result, is_terminal)."""
        t = call.tool
        if t == "DONE":
            return ToolResult(True, f"DONE: {call.args}"), True
        if t == "ABORT":
            return ToolResult(False, f"ABORT: {call.args}"), True
        if self.opts.dry_run and t in {"WRITE", "EDIT", "BASH", "GIT", "TEST", "TYPECHECK", "CHECKPOINT"}:
            return ToolResult(True, f"[dry-run] would {t} {call.args}"), False
        if t == "READ":
            return ToolResult(True, self.ctx.read_file(call.args)), False
        if t == "LS":
            target = call.args.strip() or "."
            return run_bash(REPO_ROOT, f"ls -la {target}"), False
        if t == "WRITE":
            r = write_file(REPO_ROOT, call.args, call.body)
            if r.ok:
                self.files_touched.add(call.args)
            return r, False
        if t == "EDIT":
            r = edit_file(REPO_ROOT, call.args, call.body)
            if r.ok:
                self.files_touched.add(call.args)
            return r, False
        if t == "BASH":
            return run_bash(REPO_ROOT, call.args), False
        if t == "GIT":
            return run_git(REPO_ROOT, call.args), False
        if t == "TEST":
            return run_test(REPO_ROOT), False
        if t == "TYPECHECK":
            return run_typecheck(REPO_ROOT), False
        if t == "CHECKPOINT":
            return run_checkpoint(REPO_ROOT, call.args or f"idea {self.run_id}"), False
        return ToolResult(False, f"unknown tool: {t}"), False

    def _bootstrap_context(self) -> None:
        index = self.ctx.index_repo()
        self.ctx.add("system", SYSTEM_PROMPT)
        self.ctx.add("user", f"IDEA:\n{self.opts.idea}\n\n{index}")
        self.ctx.add("user", f"Run id: {self.run_id}. Working directory: {REPO_ROOT}.")

    def _maybe_compact(self) -> None:
        if not self.ctx.needs_compact():
            return
        self.ctx.add("user", "Context near limit. Summarize all prior turns into ≤2k tokens covering: plan, tasks done, files touched, current issue, next step.")
        summary = self._llm_turn()
        self.ctx.compact(summary)
        self._audit("compact", {"new_estimate": self.ctx.estimate_tokens()})

    def run(self) -> RunResult:
        self._audit("start", asdict(self.opts))
        self._bootstrap_context()

        terminal_reason = "max_iter reached"
        terminal_ok = False

        while True:
            done, why = self.safety.exhausted()
            if done:
                terminal_reason = why
                break

            self.safety.record_iter()
            self._maybe_compact()

            try:
                response = self._llm_turn()
            except Exception as e:
                self._audit("llm_error", {"error": str(e)})
                terminal_reason = f"llm error: {e}"
                break

            call = parse_tool_call(response)
            if not call:
                self.ctx.add("user", "ERROR: no <tool>...</tool> block detected. Re-emit your last decision wrapped in a tool call.")
                self.safety.record_failure()
                self._audit("parse_fail", {"snippet": response[:300]})
                continue

            self._audit("tool_call", {"tool": call.tool, "args": call.args[:200]})
            result, terminal = self._dispatch(call)
            self._audit("tool_result", {"ok": result.ok, "out_chars": len(result.output)})

            if result.ok:
                self.safety.record_success()
            else:
                self.safety.record_failure()

            self.ctx.add("user", f"<tool_result ok={result.ok}>\n{result.output}\n</tool_result>")

            if terminal:
                terminal_reason = call.args or call.tool
                terminal_ok = result.ok and call.tool == "DONE"
                break

        # Optional deploy step
        if terminal_ok and self.opts.deploy and not self.opts.dry_run:
            dr = run_bash(REPO_ROOT, "bash scripts/deploy-dashboard.sh", timeout=600)
            self._audit("deploy", {"ok": dr.ok, "out": dr.output[:1000]})
            if not dr.ok:
                terminal_ok = False
                terminal_reason = "deploy failed: " + dr.output[:200]

        last_verify = run_test(REPO_ROOT).output[:1000] if not self.opts.dry_run else "(dry-run)"

        # Persist context and result
        self.ctx.dump(self.run_dir / "context.json")
        result = RunResult(
            run_id=self.run_id,
            ok=terminal_ok,
            reason=terminal_reason,
            iterations=self.safety.iter_count,
            files_touched=sorted(self.files_touched),
            last_verify=last_verify,
            audit_log=self.audit_path,
        )
        (self.run_dir / "result.json").write_text(json.dumps(asdict(result), default=str, indent=2), encoding="utf-8")
        self._audit("end", asdict(result))
        return result
