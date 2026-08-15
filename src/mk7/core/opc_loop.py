"""Mekong CLI 7 — OPC Business Loop (Omni Business Loop).

The infinite 24/7 loop that turns the company: OBSERVE -> DECIDE -> BUILD
-> SELL -> REVENUE -> LEARN -> OPTIMIZE -> loop.

Design contract:
- Loop is data-driven, not prompt-driven: every phase reads/writes state in
  ~/.mekong/opc/ (signals.json, revenue.json, metrics.json, loop-state.json).
- Kill rule: product with $0 revenue after KILL_CYCLES consecutive cycles is
  archived (moved to archived products, excluded from future DECIDE).
- Full-auto except money/contract: SELL auto-generates outreach/proposal
  drafts; REVENUE requires a human confirmation (never auto-records money).
- BUILD delegates to the existing orchestrate pipeline (`mk orchestrate`).
- OPTIMIZE is budget-capped (never loops forever on itself).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

OPC_DIR = Path.home() / ".mekong" / "opc"
OPC_DIR.mkdir(parents=True, exist_ok=True)

KILL_CYCLES = 2          # $0 revenue sau N cycles -> archive
OPTIMIZE_BUDGET = 1      # cycles tự optimize mỗi lần loop (chống self-loop tốn chi phí)
DEFAULT_CYCLE_HOURS = 6  # mỗi cycle loop khi omni daemon

PHASES = ["observe", "decide", "build", "sell", "revenue", "learn", "optimize"]


def _state_dir() -> Path:
    """State dir theo profile đang dùng (default → ~/.mekong/opc backward compat)."""
    try:
        from .profile import state_dir

        return state_dir()
    except Exception:
        return OPC_DIR


def _load(name: str, default: Any) -> Any:
    p = _state_dir() / name
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return default


def _save(name: str, data: Any) -> None:
    d = _state_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── Signal inbox (OBSERVE) ─────────────────────────────────────

@dataclass
class Signal:
    product: str
    kind: str          # lead | inbound | support | idea | failure | competitor
    note: str = ""
    ts: float = field(default_factory=time.time)


class SignalInbox:
    def __init__(self) -> None:
        self.data: dict[str, list[dict[str, Any]]] = _load("signals.json", {})

    def add(self, product: str, kind: str, note: str = "") -> None:
        self.data.setdefault(product, []).append({
            "kind": kind, "note": note, "ts": time.time(),
        })
        _save("signals.json", self.data)

    def list(self, product: str | None = None) -> list[tuple[str, dict[str, Any]]]:
        out = []
        for prod, sigs in self.data.items():
            if product and prod != product:
                continue
            for s in sigs:
                out.append((prod, s))
        return out

    def clear(self, product: str | None = None) -> None:
        if product:
            self.data[product] = []
        else:
            self.data = {}
        _save("signals.json", self.data)


# ── Revenue ledger (REVENUE) ───────────────────────────────────

@dataclass
class RevenueEntry:
    product: str
    amount: float
    currency: str = "USD"
    kind: str = "sale"     # sale | subscription | milestone
    confirmed_by: str = ""  # human confirm required
    ts: float = field(default_factory=time.time)


class RevenueLedger:
    def __init__(self) -> None:
        self.data: list[dict[str, Any]] = _load("revenue.json", [])

    def record(self, product: str, amount: float, currency: str = "USD",
               kind: str = "sale", confirmed_by: str = "") -> None:
        """Ghi nhận doanh thu. Bắt buộc confirmed_by (người duyệt)."""
        if not confirmed_by:
            raise ValueError("revenue requires human confirmation (confirmed_by)")
        self.data.append({
            "product": product, "amount": amount, "currency": currency,
            "kind": kind, "confirmed_by": confirmed_by, "ts": time.time(),
        })
        _save("revenue.json", self.data)

    def total_for(self, product: str, since: float = 0) -> float:
        return sum(
            e["amount"] for e in self.data
            if e["product"] == product and e["ts"] >= since
        )


# ── Metrics store (LEARN) ──────────────────────────────────────

class MetricsStore:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, Any]] = _load("metrics.json", {})

    def update(self, product: str, **kv: Any) -> None:
        m = self.data.setdefault(product, {"cycles": 0, "revenue_total": 0.0,
                                            "build_cost_hours": 0.0})
        m.update(kv)
        _save("metrics.json", self.data)

    def get(self, product: str) -> dict[str, Any]:
        return self.data.get(product, {})


# ── Loop state ─────────────────────────────────────────────────

@dataclass
class LoopState:
    cycle: int = 0
    phase: str = "observe"
    last_cycle_ts: float = 0.0
    active_products: list[str] = field(default_factory=list)
    archived_products: list[str] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    kill_cycles: int | None = None

    @classmethod
    def load(cls) -> "LoopState":
        d = _load("loop-state.json", {})
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})

    def save(self) -> None:
        _save("loop-state.json", self.__dict__)


# ── OPC Loop engine ────────────────────────────────────────────

class OpcLoop:
    def __init__(self, kill_cycles: int = KILL_CYCLES) -> None:
        self.state = LoopState.load()
        self.signals = SignalInbox()
        self.revenue = RevenueLedger()
        self.metrics = MetricsStore()
        # kill_cycles: state (persisted, cấu hình được) > default KILL_CYCLES
        if self.state.kill_cycles is None:
            self.state.kill_cycles = kill_cycles
            self.state.save()
        self.kill_cycles = self.state.kill_cycles or kill_cycles

    # ── Phase 1: OBSERVE ──
    def observe(self) -> dict[str, Any]:
        sigs = self.signals.list()
        per_product: dict[str, int] = {}
        for prod, s in sigs:
            per_product[prod] = per_product.get(prod, 0) + 1
        return {"signals": per_product, "total": len(sigs)}

    # ── Phase 2: DECIDE (rule + LLM advisory — OmniRoute-style) ──
    def decide(self, use_llm: bool = True) -> dict[str, Any]:
        # dedupe active products (chống add trùng)
        seen: set[str] = set()
        deduped: list[str] = []
        for p in self.state.active_products:
            if p not in seen:
                seen.add(p)
                deduped.append(p)
        if len(deduped) != len(self.state.active_products):
            self.state.active_products = deduped
            self.state.save()
        active = [p for p in self.state.active_products]
        kill: list[str] = []
        keep: list[str] = []
        reasons: dict[str, str] = {}
        # kill rule: $0 revenue sau kill_cycles cycles liên tiếp
        for prod in active:
            m = self.metrics.get(prod)
            rev = self.revenue.total_for(prod)
            zero_streak = m.get("zero_revenue_streak", 0)
            if rev <= 0:
                zero_streak += 1
            else:
                zero_streak = 0
            self.metrics.update(prod, zero_revenue_streak=zero_streak, revenue_total=rev)
            if zero_streak >= self.kill_cycles:
                kill.append(prod)
                reasons[prod] = f"zero revenue {zero_streak}/{self.kill_cycles} cycles"
            else:
                keep.append(prod)
                reasons[prod] = f"revenue {rev}$ · streak {zero_streak}"
        # LLM advisory (sun-tzu style — OmniRoute route model qua gateway)
        llm_advice = ""
        if use_llm and active:
            try:
                from .llm import LLMClient

                client = LLMClient(timeout=90)
                prompt = (
                    "Bạn là CEO-sun-tzu của OPC Platform. Dựa trên dữ liệu thật, đánh giá keep/kill "
                    "từng product và đề xuất 1 hành động ưu tiên.\n"
                    + "\n".join(f"- {p}: {reasons[p]}" for p in active)
                    + "\nOutput tối đa 3 dòng: per-product verdict + 1 hành động ưu tiên."
                )
                llm_advice = client.text("claude-fable-5", prompt,
                                         system="CEO advisor OPC. Ngắn gọn, dữ liệu-driven.", max_tokens=400)
            except Exception:
                llm_advice = "(llm advisory unavailable)"
        # archive killed
        for prod in kill:
            if prod in self.state.active_products:
                self.state.active_products.remove(prod)
            if prod not in self.state.archived_products:
                self.state.archived_products.append(prod)
        decision = {"cycle": self.state.cycle, "keep": keep, "kill": kill,
                    "reasons": reasons, "llm_advice": llm_advice, "ts": time.time()}
        self.state.decisions.append(decision)
        self.state.save()
        return decision

    # ── Phase 3: BUILD (delegate to mk orchestrate — thật khi auto_build) ──
    def build(self, product: str, task: str, dry_run: bool = True) -> dict[str, Any]:
        if dry_run:
            return {"product": product, "status": "dry-run",
                    "note": "pipeline orchestrate (bỏ qua ở dry-run)"}
        proc = subprocess.run(
            [str(Path.home() / "bin" / "mk"), "orchestrate", task],
            capture_output=True, text=True, timeout=600,
        )
        return {"product": product, "status": "ok" if proc.returncode == 0 else "fail",
                "exit": proc.returncode, "output": (proc.stdout or "")[-300:]}

    # ── Phase 4: SELL (LLM outreach draft — human closes) ──
    def sell(self, product: str, dry_run: bool = True) -> dict[str, Any]:
        m = self.metrics.get(product)
        rev = self.revenue.total_for(product)
        draft = ""
        try:
            from .llm import LLMClient

            client = LLMClient(timeout=90)
            prompt = (
                f"Viết outreach draft tiếng Việt cho product '{product}' (OPC Platform).\n"
                f"Điểm thật: revenue={rev}$ · cycles={m.get('cycles', 0)} · "
                f"zero_streak={m.get('zero_revenue_streak', 0)}\n"
                "Output: hook 1 dòng + value prop + CTA hẹn call. Ngắn, không phồng."
            )
            draft = client.text("claude-fable-5", prompt,
                                system="Bạn là AE OPC Platform.", max_tokens=400)
        except Exception:
            draft = f"Outreach draft for {product}: giá trị = {rev}$ đã ghi nhận"
        return {
            "product": product,
            "draft": draft,
            "status": "draft-ready" if dry_run else "sent",
            "note": "contract/tiền chờ human confirm (confirmed_by)",
        }

    # ── Phase 5: REVENUE (human-only, không auto) ──
    def revenue_phase(self, product: str) -> dict[str, Any]:
        total = self.revenue.total_for(product)
        return {"product": product, "total": total,
                "note": "ghi nhận mới bắt buộc confirmed_by người"}

    # ── Phase 6: LEARN ──
    def learn(self, product: str) -> dict[str, Any]:
        m = self.metrics.get(product)
        rev = self.revenue.total_for(product)
        hours = m.get("build_cost_hours", 0) or 1
        return {"product": product, "revenue": rev,
                "revenue_per_hour": round(rev / hours, 2),
                "cycles": m.get("cycles", 0)}

    # ── Phase 7: OPTIMIZE (budget-capped) ──
    def optimize(self, product: str) -> dict[str, Any]:
        if self.state.cycle % (OPTIMIZE_BUDGET + 1) != 0:
            return {"product": product, "skipped": True,
                    "reason": "optimize budget cap (1 lần mỗi N cycles)"}
        # KISS: gợi ý tối ưu từ metrics — không self-rewrite loop (chống vòng lặp vô hạn)
        m = self.metrics.get(product)
        rev = self.revenue.total_for(product)
        if rev == 0 and m.get("cycles", 0) > 0:
            hint = "XEM XÉT kill/đổi positioning — 0 doanh thu"
        elif rev > 0:
            hint = "Giữ nguyên, tăng budget build"
        else:
            hint = "Cần signal mới để decide"
        return {"product": product, "hint": hint}

    # ── Run one full cycle ──
    def run_cycle(self, dry_run: bool = True, auto_build: bool = False,
                  use_llm: bool = True) -> dict[str, Any]:
        self.state.cycle += 1
        self.state.phase = "observe"
        report: dict[str, Any] = {"cycle": self.state.cycle}

        # Tăng cycles cho MỌI active TRƯỚC decide (killed vẫn được đếm)
        for prod in list(self.state.active_products):
            m = self.metrics.get(prod)
            self.metrics.update(prod, cycles=m.get("cycles", 0) + 1)

        report["observe"] = self.observe()
        self.state.phase = "decide"
        report["decide"] = self.decide(use_llm=use_llm)

        for prod in self.state.active_products:
            self.state.phase = "build"
            report.setdefault("build", {})[prod] = self.build(
                prod, f"Tiếp tục phát triển {prod}", dry_run=not auto_build)
            self.state.phase = "sell"
            report.setdefault("sell", {})[prod] = self.sell(prod, dry_run)
            self.state.phase = "revenue"
            report.setdefault("revenue", {})[prod] = self.revenue_phase(prod)
            self.state.phase = "learn"
            report.setdefault("learn", {})[prod] = self.learn(prod)
            self.state.phase = "optimize"
            report.setdefault("optimize", {})[prod] = self.optimize(prod)

        self.state.phase = "done"
        self.state.last_cycle_ts = time.time()
        self.state.save()
        return report
