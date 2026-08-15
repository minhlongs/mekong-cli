"""Mekong CLI 7 — Orchestrate pipeline (port of Claude Code /orchestrate).

5-phase pipeline for a solo-CEO harness:
  PLAN (kongming/strategist) -> PLAN GATE (suntzu, repeat-until <=3 rounds)
  -> EXECUTE (dispatch_node per step) -> RESULT GATE (suntzu, repeat-until)
  -> SHIP (commit/PR/deploy/smoke) -> go-live report.

Design contract (aligned with ~/.claude/commands/orchestrate.md):
- No hard stop: AMEND loops up to 3 rounds, each round ONLY re-verifies the
  previous round's conditions; new findings go to "Out-of-scope observations".
- CONDITIONAL PASS: when all previous conditions are satisfied (even with new
  observations), verdict escalates to CONDITIONAL PASS and the pipeline
  CONTINUES (no stop). MED/LOW findings become escrow TODOs.
- File-based handoff in .orchestrate/latest/ (task/plan/plan-verdict/execution/
  result-verdict/ship-report).
- SHIP phase: commit -> PR -> deploy (repo doctrine) -> curl smoke -> report.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .llm import LLMClient
from .models import resolve_or_fallback

ORCH_DIR = Path(".orchestrate") / "latest"

MAX_GATE_ROUNDS = 3

PLAN_SYSTEM = (
    "You are Khổng Minh (kongming) — the strategist planner. Given a task, produce "
    "a concrete plan with: Reframed problem, Work checklist (each step with "
    "acceptance criteria), Risks & gates, agent suggestion per step, and a Ship "
    "plan (commit -> PR -> deploy -> smoke). Be honest about feasibility. "
    "Do not ask questions; make reasonable assumptions and record them."
)

GATE_SYSTEM = (
    "You are Tôn Tử (suntzu) — the evaluator and supervisor. You judge, you never "
    "implement. Verdict first line: PASS / CONDITIONAL PASS / AMEND / FAIL + ROUND: n.\n"
    "Rules: cite evidence (paths, commands, output). Scope freeze: when given the "
    "previous round's conditions, ONLY re-verify those; new findings go to "
    "'Out-of-scope observations' and MUST NOT block. If all previous conditions are "
    "SATISFIED -> verdict CONDITIONAL PASS (continue), never AMEND on new findings "
    "when old ones are satisfied. Only HIGH severity with real failing evidence "
    "forces AMEND."
)

SHIP_STEPS = (
    "1) git status/diff review; 2) commit (conventional) via git; 3) push branch; "
    "4) gh pr create (if repo uses PRs) or direct push per repo doctrine; "
    "5) deploy per repo doctrine (read package.json scripts / CLAUDE.deploy.md / "
    "docs/deploy*.md); 6) curl smoke the production URL; 7) verify live SHA == "
    "local SHA when deploy proof required."
)


@dataclass
class GateResult:
    verdict: str  # PASS | CONDITIONAL PASS | AMEND | FAIL
    round: int = 1
    conditions: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def can_proceed(self) -> bool:
        return self.verdict in ("PASS", "CONDITIONAL PASS")


@dataclass
class PipelineResult:
    ok: bool
    phase: str = ""
    plan: str = ""
    plan_verdict: str = ""
    execution: str = ""
    result_verdict: str = ""
    ship_report: str = ""
    error: str = ""
    escrow_todos: list[str] = field(default_factory=list)


class OrchestrateError(RuntimeError):
    pass


def _ensure_dir() -> Path:
    ORCH_DIR.mkdir(parents=True, exist_ok=True)
    return ORCH_DIR


def _write(name: str, content: str) -> Path:
    p = _ensure_dir() / name
    p.write_text(content)
    return p


def _read(name: str) -> str:
    p = ORCH_DIR / name
    if not p.exists():
        raise OrchestrateError(f"missing handoff file: {p}")
    return p.read_text()


def _llm_text(
    client: LLMClient,
    model_key: str,
    prompt: str,
    system: str,
    max_tokens: int = 4096,
) -> str:
    entry = resolve_or_fallback(model_key)
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    data = client.chat(entry.id, messages, max_tokens=max_tokens, timeout=300)
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError):
        return json.dumps(data)[:500]


def _parse_gate(raw: str) -> GateResult:
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    first = lines[0].upper() if lines else ""
    verdict = "FAIL"
    for v in ("CONDITIONAL PASS", "PASS", "AMEND", "FAIL"):
        if first.startswith(v):
            verdict = v
            break
    round_n = 1
    for ln in lines[:3]:
        if "ROUND" in ln.upper():
            m = __import__("re").search(r"ROUND\s*:?\s*(\d+)", ln, __import__("re").I)
            if m:
                round_n = int(m.group(1))
    conditions: list[str] = []
    observations: list[str] = []
    in_cond = in_obs = False
    for ln in lines[1:]:
        low = ln.lower()
        if low.startswith("condition"):
            in_cond, in_obs = True, False
            continue
        if low.startswith("out-of-scope") or low.startswith("observation"):
            in_cond, in_obs = False, True
            continue
        if ln.startswith(("evidence", "findings", "scope check", "##")):
            in_cond = in_obs = False
            continue
        if in_cond and ln:
            conditions.append(ln)
        elif in_obs and ln:
            observations.append(ln)
    return GateResult(verdict=verdict, round=round_n, conditions=conditions,
                      observations=observations, raw=raw)


# ── Phase 1: PLAN ─────────────────────────────────────────────

def phase_plan(client: LLMClient, task: str, model_key: str = "fable") -> str:
    _write("task.md", task)
    prompt = (
        f"TASK: {task}\n\n"
        "Write the full plan into .orchestrate/latest/plan.md (overwrite) using the "
        "Write-file convention: produce the plan text, then I will persist it. "
        "Plan must include: Reframed problem, Work checklist (steps + acceptance "
        "criteria), Risks & gates, agent per step, Ship plan."
    )
    raw = _llm_text(client, model_key, prompt, PLAN_SYSTEM, max_tokens=8192)
    # best-effort: strip fences
    plan = raw.strip()
    if plan.startswith("```"):
        plan = plan.strip("`").strip()
        if plan.startswith(("markdown", "md")):
            plan = plan.split("\n", 1)[-1].strip()
    _write("plan.md", plan)
    return plan


# ── Phase 2 / 4: GATES ─────────────────────────────────────────

def _run_gate(
    client: LLMClient,
    model_key: str,
    prompt: str,
    model_role: str = "fable",
) -> GateResult:
    raw = _llm_text(client, model_key, prompt, GATE_SYSTEM, max_tokens=4096)
    return _parse_gate(raw)


def phase_plan_gate(
    client: LLMClient,
    model_key: str = "fable",
    prev_conditions: list[str] | None = None,
    round_n: int = 1,
) -> GateResult:
    plan = _read("plan.md")
    task = _read("task.md")
    cond_block = ""
    if prev_conditions:
        cond_block = (
            "PREVIOUS ROUND CONDITIONS (verify ONLY these, with commands + expected "
            f"output):\n{chr(10).join(f'- {c}' for c in prev_conditions)}\n"
        )
    prompt = (
        f"ROUND {round_n}. Task: {task}\n\nPlan (from .orchestrate/latest/plan.md):\n{plan[:12000]}\n\n"
        f"{cond_block}"
        "Write your verdict (first line: PASS / CONDITIONAL PASS / AMEND / FAIL + "
        "ROUND: n) to .orchestrate/latest/plan-verdict.md, then repeat the verdict "
        "in your reply."
    )
    result = _run_gate(client, model_key, prompt)
    _write("plan-verdict.md", result.raw)
    result.round = round_n
    return result


def phase_result_gate(
    client: LLMClient,
    model_key: str = "fable",
    prev_conditions: list[str] | None = None,
    round_n: int = 1,
) -> GateResult:
    plan = _read("plan.md")
    task = _read("task.md")
    execution = _read("execution.md")
    cond_block = ""
    if prev_conditions:
        cond_block = (
            "PREVIOUS ROUND CONDITIONS (verify ONLY these):\n"
            f"{chr(10).join(f'- {c}' for c in prev_conditions)}\n"
        )
    prompt = (
        f"ROUND {round_n}. Task: {task}\n\nPlan: {plan[:8000]}\n\n"
        f"Execution results (from .orchestrate/latest/execution.md):\n{execution[:12000]}\n\n"
        f"{cond_block}"
        "Write your verdict (first line: PASS / CONDITIONAL PASS / AMEND / FAIL + "
        "ROUND: n) to .orchestrate/latest/result-verdict.md, then repeat the "
        "verdict in your reply."
    )
    result = _run_gate(client, model_key, prompt)
    _write("result-verdict.md", result.raw)
    result.round = round_n
    return result


# ── Phase 3: EXECUTE ───────────────────────────────────────────

def phase_execute(
    client: LLMClient,
    task: str,
    agent: str = "eng",
    max_tokens: int = 4096,
) -> str:
    """Execute the plan via dispatch_node (tool-capable loop, max_steps)."""
    from .agents import get_agent
    from .dispatch import dispatch_node
    from .graph import Node

    agent_obj = get_agent(agent)
    model_key = agent_obj.model if agent_obj else "sonnet"
    plan = _read("plan.md")
    node = Node(
        id="execute",
        task=(
            f"You are the {agent} agent. Execute the plan below. Use tools "
            "(bash-test, write, read, grep, glob, edit) as needed. Record progress "
            "into .orchestrate/latest/execution.md (append per step: what was done, "
            "tests run, results). Finish with RESULT: <summary>.\n\n"
            f"TASK: {task}\n\nPLAN:\n{plan[:16000]}"
        ),
        agent=agent,
    )
    out = dispatch_node(node, {}, client=client, max_tokens=max_tokens, max_steps=8)
    raw = str(out.get("result") or out.get("llm") or "")
    tools = out.get("tools") or []
    if tools:
        tool_log = "\n\n## Tool executions\n"
        for t in tools:
            if isinstance(t, dict):
                tool_log += f"- tool={t.get('tool')} ok={t.get('ok')} output={str(t.get('output'))[:400]}\n"
            else:
                tool_log += f"- {str(t)[:400]}\n"
        raw = raw + tool_log
    _write("execution.md", raw.strip())
    return raw


# ── Phase 5: SHIP ──────────────────────────────────────────────

def phase_ship(dry_run: bool = False) -> str:
    """Commit -> push -> deploy (repo doctrine) -> curl smoke. Returns report."""
    from .sop import build_ship_commands  # late import to avoid cycle

    steps = build_ship_commands(Path.cwd())
    lines = [f"# Ship Report — {time.strftime('%Y-%m-%d %H:%M:%S %Z')}", ""]
    for i, (desc, cmd, check) in enumerate(steps, 1):
        lines.append(f"## Step {i}: {desc}")
        if dry_run:
            lines.append(f"`{cmd}`  (dry-run — not executed)")
            continue
        try:
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                  timeout=600)
            out = (proc.stdout or "")[-1500:]
            err = (proc.stderr or "")[-800:]
            ok = proc.returncode == 0
            lines.append(f"- Exit: {proc.returncode} {'OK' if ok else 'FAIL'}")
            if out.strip():
                lines.append(f"- Output: {out.strip()[:600]}")
            if not ok and err.strip():
                lines.append(f"- Error: {err.strip()[:400]}")
            if check and ok:
                lines.append(f"- Verify: {check}")
        except subprocess.TimeoutExpired:
            lines.append("- Exit: TIMEOUT (>600s)")
    report = "\n".join(lines)
    _write("ship-report.md", report)
    return report


# ── Pipeline driver ────────────────────────────────────────────

def run_pipeline(
    task: str,
    client: LLMClient | None = None,
    dry_run: bool = False,
    execute_agent: str = "eng",
) -> PipelineResult:
    client = client or LLMClient(timeout=300)
    result = PipelineResult(ok=False)
    try:
        # Phase 1
        result.phase = "plan"
        result.plan = phase_plan(client, task)

        # Phase 2 — plan gate (repeat-until, max 3)
        result.phase = "plan-gate"
        prev_conds: list[str] | None = None
        gate = phase_plan_gate(client, prev_conditions=prev_conds, round_n=1)
        result.plan_verdict = gate.raw
        for rnd in range(2, MAX_GATE_ROUNDS + 1):
            if gate.can_proceed:
                break
            if gate.verdict == "FAIL":
                result.error = f"plan gate FAIL round {gate.round}: {gate.raw[:600]}"
                return result
            # AMEND -> re-plan (best-effort single call with conditions) then re-gate
            result.plan = phase_plan(client, f"{task}\n\nAMEND ROUND {rnd}: fix these conditions:\n"
                                            + "\n".join(f"- {c}" for c in gate.conditions[:8]))
            gate = phase_plan_gate(client, prev_conditions=gate.conditions, round_n=rnd)
            result.plan_verdict = gate.raw
            if gate.can_proceed:
                break
            # escape hatch: all old conditions satisfied? model says so in verdict
            if "SATISFIED" in gate.raw.upper() and "CONDITIONAL" in gate.raw.upper():
                break
        if not gate.can_proceed:
            result.error = (
                f"plan gate not converged after {MAX_GATE_ROUNDS} rounds: "
                f"{gate.verdict} — {gate.raw[:500]}"
            )
            return result

        # Phase 3 — execute
        result.phase = "execute"
        result.execution = phase_execute(client, task, agent=execute_agent)

        # Phase 4 — result gate (repeat-until, max 3)
        result.phase = "result-gate"
        prev = None
        gate = phase_result_gate(client, prev_conditions=prev, round_n=1)
        result.result_verdict = gate.raw
        for rnd in range(2, MAX_GATE_ROUNDS + 1):
            if gate.can_proceed:
                break
            if gate.verdict == "FAIL":
                result.error = f"result gate FAIL round {gate.round}: {gate.raw[:600]}"
                return result
            result.execution = phase_execute(
                client, f"{task}\n\nAMEND ROUND {rnd}: fix these conditions:\n"
                        + "\n".join(f"- {c}" for c in gate.conditions[:8]),
                agent=execute_agent,
            )
            gate = phase_result_gate(client, prev_conditions=gate.conditions, round_n=rnd)
            result.result_verdict = gate.raw
            if gate.can_proceed:
                break
        if not gate.can_proceed:
            result.error = (
                f"result gate not converged after {MAX_GATE_ROUNDS} rounds: "
                f"{gate.verdict} — {gate.raw[:500]}"
            )
            return result

        # Phase 5 — ship
        result.phase = "ship"
        result.ship_report = phase_ship(dry_run=dry_run)

        result.ok = True
        return result
    except Exception as e:  # noqa: BLE001
        result.error = f"{result.phase}: {e}"
        return result


# ── SOP integration (24/7 operations) ──────────────────────────

def run_sop_pipeline(
    sop: "SopDocument",
    client: LLMClient | None = None,
    dry_run: bool = False,
    execute_agent: str = "eng",
) -> PipelineResult:
    task = (
        f"Execute SOP '{sop.name}' (layer {sop.layer}) according to its steps.\n\n"
        f"SOP content:\n{sop.body[:12000]}"
    )
    return run_pipeline(task, client=client, dry_run=dry_run, execute_agent=execute_agent)
