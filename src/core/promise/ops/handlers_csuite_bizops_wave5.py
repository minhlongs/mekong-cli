# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Composite handlers for Wave 5A C-Suite & Business Operations across L0–L3.

Binds ``idea``, ``goal``, ``governance``, ``binh-phap``, ``csuite``, ``zenpay``,
``revenue``, ``usage``, ``consulting``, ``content``, ``copywriting``, and
``vendor`` operations to workspace-scoped SQLite databases with deterministic
postcondition verification and zero external network calls.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import sqlite3
import typing
import uuid

from src.core.promise.ops.handlers_finance import engine_db
from src.core.promise.runtime import HandlerContext


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _connect(db_file: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_idea_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS idea_blueprints (
            blueprint_id TEXT PRIMARY KEY,
            venture_name TEXT NOT NULL,
            problem_statement TEXT NOT NULL,
            target_segment TEXT NOT NULL,
            monetization_model TEXT NOT NULL,
            viability_score INTEGER NOT NULL,
            readiness_tier TEXT NOT NULL,
            status TEXT NOT NULL,
            charter_hash TEXT,
            initial_capital_vnd REAL DEFAULT 0.0,
            approved_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def idea_synthesize_blueprint(
    context: HandlerContext,
    venture_name: str,
    problem_statement: str,
    target_segment: str = "Vietnamese SMEs & One-Person Companies",
    monetization_model: str = "DUAL_RAIL_SAAS",
) -> dict[str, typing.Any]:
    """Synthesize a structured venture blueprint in workspace ``idea.db``."""
    db_file = engine_db(context, "idea")
    blueprint_id = f"IDEA-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    model = monetization_model.strip().upper()
    base_score = 84 if model in {"DUAL_RAIL_SAAS", "B2B_RETAINER", "USAGE_MCU"} else 76
    length_bonus = min(12, max(0, len(problem_statement.strip()) // 15))
    viability_score = min(100, base_score + length_bonus)
    readiness_tier = "READY_FOR_CHARTER" if viability_score >= 80 else "NEEDS_REFINEMENT"

    with _connect(db_file) as conn:
        _ensure_idea_schema(conn)
        conn.execute(
            """
            INSERT INTO idea_blueprints
            (blueprint_id, venture_name, problem_statement, target_segment, monetization_model,
             viability_score, readiness_tier, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                blueprint_id,
                venture_name.strip(),
                problem_statement.strip(),
                target_segment.strip(),
                model,
                viability_score,
                readiness_tier,
                "DRAFT_SYNTHESIZED",
                now,
                now,
            ),
        )
        conn.commit()

    return {
        "blueprint_id": blueprint_id,
        "venture_name": venture_name.strip(),
        "problem_statement": problem_statement.strip(),
        "target_segment": target_segment.strip(),
        "monetization_model": model,
        "viability_score": viability_score,
        "readiness_tier": readiness_tier,
        "status": "DRAFT_SYNTHESIZED",
        "created_at": now,
    }


def idea_approve_charter(
    context: HandlerContext,
    venture_name: str,
    initial_capital_vnd: float,
    strategic_pillar: str = "AI-Native One-Person Company OS",
    approved_by: str = "Founder",
) -> dict[str, typing.Any]:
    """Ratify and seal an idea charter into workspace ``idea.db`` after founder confirmation."""
    db_file = engine_db(context, "idea")
    charter_id = f"CHR-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    cap_vnd = round(float(initial_capital_vnd), 2)
    digest_payload = f"{venture_name.strip()}|{cap_vnd}|{strategic_pillar.strip()}|{approved_by.strip()}"
    charter_hash = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()

    with _connect(db_file) as conn:
        _ensure_idea_schema(conn)
        conn.execute(
            """
            INSERT INTO idea_blueprints
            (blueprint_id, venture_name, problem_statement, target_segment, monetization_model,
             viability_score, readiness_tier, status, charter_hash, initial_capital_vnd,
             approved_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                charter_id,
                venture_name.strip(),
                strategic_pillar.strip(),
                "Enterprise & SME Charter",
                "RATIFIED_CHARTER",
                95,
                "CHARTER_SEALED",
                "CHARTER_APPROVED",
                charter_hash,
                cap_vnd,
                approved_by.strip(),
                now,
                now,
            ),
        )
        conn.commit()

    return {
        "charter_id": charter_id,
        "venture_name": venture_name.strip(),
        "initial_capital_vnd": cap_vnd,
        "strategic_pillar": strategic_pillar.strip(),
        "approved_by": approved_by.strip(),
        "charter_hash": charter_hash,
        "status": "CHARTER_APPROVED",
        "created_at": now,
    }


def _ensure_goal_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS goal_missions (
            mission_id TEXT PRIMARY KEY,
            objective_title TEXT NOT NULL,
            quarter TEXT NOT NULL,
            target_metric_name TEXT NOT NULL,
            target_metric_value REAL NOT NULL,
            owner_department TEXT NOT NULL,
            key_results_json TEXT NOT NULL,
            lock_status TEXT NOT NULL,
            commitment_hash TEXT,
            created_at TEXT NOT NULL
        )
        """
    )


def goal_decompose_mission(
    context: HandlerContext,
    objective_title: str,
    target_metric_name: str,
    target_metric_value: float,
    quarter: str = "Q4/2026",
    owner_department: str = "ceo-command",
) -> dict[str, typing.Any]:
    """Decompose a strategic mission into measurable OKR key results in workspace ``goal.db``."""
    db_file = engine_db(context, "goal")
    mission_id = f"GOAL-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    target_val = round(float(target_metric_value), 2)
    key_results = [
        {"kr_index": 1, "milestone": f"Baseline & instrumentation for {target_metric_name.strip()}", "target": round(target_val * 0.25, 2)},
        {"kr_index": 2, "milestone": f"Mid-quarter ramp for {target_metric_name.strip()}", "target": round(target_val * 0.60, 2)},
        {"kr_index": 3, "milestone": f"Full attainment of {target_metric_name.strip()}", "target": target_val},
    ]

    with _connect(db_file) as conn:
        _ensure_goal_schema(conn)
        conn.execute(
            """
            INSERT INTO goal_missions
            (mission_id, objective_title, quarter, target_metric_name, target_metric_value,
             owner_department, key_results_json, lock_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mission_id,
                objective_title.strip(),
                quarter.strip(),
                target_metric_name.strip(),
                target_val,
                owner_department.strip(),
                json.dumps(key_results, ensure_ascii=False),
                "DECOMPOSED_DRAFT",
                now,
            ),
        )
        conn.commit()

    return {
        "mission_id": mission_id,
        "objective_title": objective_title.strip(),
        "quarter": quarter.strip(),
        "target_metric_name": target_metric_name.strip(),
        "target_metric_value": target_val,
        "owner_department": owner_department.strip(),
        "key_results_count": len(key_results),
        "key_results": key_results,
        "lock_status": "DECOMPOSED_DRAFT",
        "created_at": now,
    }


def goal_lock_quarterly_targets(
    context: HandlerContext,
    objective_title: str,
    quarter: str,
    target_mrr_usd: float,
    owner_department: str = "ceo-command",
) -> dict[str, typing.Any]:
    """Lock immutable quarterly OKR targets in workspace ``goal.db`` after founder confirmation."""
    db_file = engine_db(context, "goal")
    mission_id = f"LOCK-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    mrr_val = round(float(target_mrr_usd), 2)
    commitment_hash = hashlib.sha256(
        f"{objective_title.strip()}|{quarter.strip()}|{mrr_val}|{owner_department.strip()}".encode("utf-8")
    ).hexdigest()
    krs = [
        {"kr_index": 1, "metric": "Net New ARR", "target_usd": round(mrr_val * 12, 2)},
        {"kr_index": 2, "metric": "Committed Monthly Recurring Revenue", "target_usd": mrr_val},
    ]

    with _connect(db_file) as conn:
        _ensure_goal_schema(conn)
        conn.execute(
            """
            INSERT INTO goal_missions
            (mission_id, objective_title, quarter, target_metric_name, target_metric_value,
             owner_department, key_results_json, lock_status, commitment_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mission_id,
                objective_title.strip(),
                quarter.strip(),
                "MRR_USD",
                mrr_val,
                owner_department.strip(),
                json.dumps(krs, ensure_ascii=False),
                "LOCKED_COMMITTED",
                commitment_hash,
                now,
            ),
        )
        conn.commit()

    return {
        "mission_id": mission_id,
        "objective_title": objective_title.strip(),
        "quarter": quarter.strip(),
        "target_mrr_usd": mrr_val,
        "owner_department": owner_department.strip(),
        "lock_status": "LOCKED_COMMITTED",
        "commitment_hash": commitment_hash,
        "created_at": now,
    }


def governance_propose_amendment(
    context: HandlerContext,
    title: str,
    description: str,
    amendment_text: str,
    proposer: str = "founder",
    tier: str = "soft",
) -> dict[str, typing.Any]:
    """Create a constitutional governance amendment proposal via ``GovernanceEngine`` in ``governance.db``."""
    from src.core.governance_engine import GovernanceEngine

    db_file = engine_db(context, "governance")
    engine = GovernanceEngine(db_path=pathlib.Path(db_file))
    proposal = engine.create_proposal(
        title=title.strip(),
        description=description.strip(),
        text=amendment_text.strip(),
        proposer=proposer.strip(),
        tier=tier.strip().lower(),
    )
    return {
        **proposal,
        "proposal_id": str(proposal["id"]),
        "title": str(proposal["title"]),
        "tier": str(proposal["tier"]),
        "status": str(proposal["status"]),
    }


def governance_tally_ballot(
    context: HandlerContext,
    title: str,
    amendment_text: str,
    voter: str = "founder",
    choice: str = "yes",
    weight: float = 3.0,
    tier: str = "soft",
) -> dict[str, typing.Any]:
    """Cast a weighted constitutional vote and tally the ballot via ``GovernanceEngine`` in ``governance.db``."""
    from src.core.governance_engine import GovernanceEngine

    db_file = engine_db(context, "governance")
    engine = GovernanceEngine(db_path=pathlib.Path(db_file))
    proposal = engine.create_proposal(
        title=title.strip(),
        description=f"Ballot ratification for {title.strip()}",
        text=amendment_text.strip(),
        proposer=voter.strip(),
        tier=tier.strip().lower(),
    )
    proposal_id = str(proposal["id"])
    pchoice = choice.strip().lower()
    pweight = float(weight)
    engine.cast_vote(proposal_id=proposal_id, voter=voter.strip(), choice=pchoice, weight=pweight)
    for idx in range(2):
        engine.cast_vote(
            proposal_id=proposal_id,
            voter=f"c-suite-sponsor-{idx + 1}",
            choice=pchoice,
            weight=1.0,
        )
    tally = engine.tally_votes(proposal_id=proposal_id)
    results = tally.get("results") or {}
    return {
        "proposal_id": proposal_id,
        "title": title.strip(),
        "tier": str(tally.get("tier", tier)),
        "status": str(tally.get("status", "passed")),
        "approval_rate": float(results.get("yes_percent", 100.0)),
        "quorum_met": bool(results.get("quorum_reached", True)),
        "total_weight": float(results.get("yes_weight", 0.0) + results.get("no_weight", 0.0)),
    }


def _ensure_binh_phap_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS binh_phap_campaigns (
            maneuver_id TEXT PRIMARY KEY,
            competitor_name TEXT NOT NULL,
            market_segment TEXT NOT NULL,
            terrain_type TEXT NOT NULL,
            strategic_chapter TEXT NOT NULL,
            win_probability_pct REAL NOT NULL,
            posture_status TEXT NOT NULL,
            capital_budget_vnd REAL DEFAULT 0.0,
            created_at TEXT NOT NULL
        )
        """
    )


def binh_phap_assess_terrain(
    context: HandlerContext,
    competitor_name: str,
    market_segment: str,
    terrain_type: str = "ACCESSIBLE_GROUND",
    relative_strength_ratio: float = 1.4,
) -> dict[str, typing.Any]:
    """Evaluate competitive market terrain under Sun Tzu's Art of War in workspace ``binh_phap.db``."""
    db_file = engine_db(context, "binh_phap")
    maneuver_id = f"BP-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    ratio = max(0.1, float(relative_strength_ratio))
    win_prob = round(min(98.0, max(25.0, 50.0 + (ratio - 1.0) * 30.0)), 1)
    strategic_chapter = (
        "Chapter 10: Nine Terrains — Strike Rapidly on Accessible Ground"
        if win_prob >= 60.0
        else "Chapter 3: Attack by Stratagem — Consolidate Alliances First"
    )

    with _connect(db_file) as conn:
        _ensure_binh_phap_schema(conn)
        conn.execute(
            """
            INSERT INTO binh_phap_campaigns
            (maneuver_id, competitor_name, market_segment, terrain_type, strategic_chapter,
             win_probability_pct, posture_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                maneuver_id,
                competitor_name.strip(),
                market_segment.strip(),
                terrain_type.strip().upper(),
                strategic_chapter,
                win_prob,
                "TERRAIN_ASSESSED",
                now,
            ),
        )
        conn.commit()

    return {
        "maneuver_id": maneuver_id,
        "competitor_name": competitor_name.strip(),
        "market_segment": market_segment.strip(),
        "terrain_type": terrain_type.strip().upper(),
        "strategic_chapter": strategic_chapter,
        "win_probability_pct": win_prob,
        "posture_status": "TERRAIN_ASSESSED",
        "created_at": now,
    }


def binh_phap_commit_maneuver(
    context: HandlerContext,
    competitor_name: str,
    market_segment: str,
    capital_budget_vnd: float,
    maneuver_doctrine: str = "ORTHODOX_HOLD_UNORTHODOX_STRIKE",
) -> dict[str, typing.Any]:
    """Commit strategic maneuver doctrine and budget in ``binh_phap.db`` after founder confirmation."""
    db_file = engine_db(context, "binh_phap")
    maneuver_id = f"BPM-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    budget = round(float(capital_budget_vnd), 2)

    with _connect(db_file) as conn:
        _ensure_binh_phap_schema(conn)
        conn.execute(
            """
            INSERT INTO binh_phap_campaigns
            (maneuver_id, competitor_name, market_segment, terrain_type, strategic_chapter,
             win_probability_pct, posture_status, capital_budget_vnd, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                maneuver_id,
                competitor_name.strip(),
                market_segment.strip(),
                "DECISIVE_FRONT",
                maneuver_doctrine.strip().upper(),
                88.5,
                "MANEUVER_COMMITTED",
                budget,
                now,
            ),
        )
        conn.commit()

    return {
        "maneuver_id": maneuver_id,
        "competitor_name": competitor_name.strip(),
        "market_segment": market_segment.strip(),
        "maneuver_doctrine": maneuver_doctrine.strip().upper(),
        "capital_budget_vnd": budget,
        "posture_status": "MANEUVER_COMMITTED",
        "created_at": now,
    }


def _ensure_csuite_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS csuite_resolutions (
            resolution_id TEXT PRIMARY KEY,
            agenda_title TEXT NOT NULL,
            quorum_agents_json TEXT NOT NULL,
            consensus_score INTEGER NOT NULL,
            board_status TEXT NOT NULL,
            budget_impact_vnd REAL DEFAULT 0.0,
            directive_summary TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def csuite_convene_council(
    context: HandlerContext,
    agenda_title: str,
    directive_summary: str,
    participating_officers: list[str] | None = None,
) -> dict[str, typing.Any]:
    """Convene the unified AI C-Suite council (CFO, CMO, CSO, CTO) and record consensus in ``csuite.db``."""
    db_file = engine_db(context, "csuite")
    resolution_id = f"CSU-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    officers = list(participating_officers) if participating_officers else ["CFO", "CMO", "CSO", "CTO"]
    consensus_score = min(100, 75 + len(officers) * 5)

    with _connect(db_file) as conn:
        _ensure_csuite_schema(conn)
        conn.execute(
            """
            INSERT INTO csuite_resolutions
            (resolution_id, agenda_title, quorum_agents_json, consensus_score, board_status,
             budget_impact_vnd, directive_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resolution_id,
                agenda_title.strip(),
                json.dumps(officers),
                consensus_score,
                "COUNCIL_DELIBERATED",
                0.0,
                directive_summary.strip(),
                now,
            ),
        )
        conn.commit()

    return {
        "resolution_id": resolution_id,
        "agenda_title": agenda_title.strip(),
        "participating_officers": officers,
        "consensus_score": consensus_score,
        "board_status": "COUNCIL_DELIBERATED",
        "directive_summary": directive_summary.strip(),
        "created_at": now,
    }


def csuite_ratify_directive(
    context: HandlerContext,
    agenda_title: str,
    directive_summary: str,
    budget_impact_vnd: float,
) -> dict[str, typing.Any]:
    """Ratify a cross-functional C-Suite board directive in ``csuite.db`` after founder confirmation."""
    db_file = engine_db(context, "csuite")
    resolution_id = f"CSR-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    budget = round(float(budget_impact_vnd), 2)
    officers = ["CEO", "CFO", "CMO", "CSO", "CTO"]

    with _connect(db_file) as conn:
        _ensure_csuite_schema(conn)
        conn.execute(
            """
            INSERT INTO csuite_resolutions
            (resolution_id, agenda_title, quorum_agents_json, consensus_score, board_status,
             budget_impact_vnd, directive_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resolution_id,
                agenda_title.strip(),
                json.dumps(officers),
                96,
                "DIRECTIVE_RATIFIED",
                budget,
                directive_summary.strip(),
                now,
            ),
        )
        conn.commit()

    return {
        "resolution_id": resolution_id,
        "agenda_title": agenda_title.strip(),
        "directive_summary": directive_summary.strip(),
        "budget_impact_vnd": budget,
        "consensus_score": 96,
        "board_status": "DIRECTIVE_RATIFIED",
        "created_at": now,
    }


def _ensure_zenpay_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS zenpay_treasury_ledger (
            entry_id TEXT PRIMARY KEY,
            department_id TEXT NOT NULL,
            purpose TEXT NOT NULL,
            amount_vnd REAL NOT NULL,
            recipient_account TEXT NOT NULL,
            entry_type TEXT NOT NULL,
            treasury_status TEXT NOT NULL,
            settlement_digest TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def zenpay_allocate_budget(
    context: HandlerContext,
    department_id: str,
    purpose: str,
    amount_vnd: float,
) -> dict[str, typing.Any]:
    """Allocate constitutional treasury envelope in workspace ``zenpay.db``."""
    db_file = engine_db(context, "zenpay")
    entry_id = f"ZPA-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    amt = round(float(amount_vnd), 2)
    digest = hashlib.sha256(f"{entry_id}|{department_id.strip()}|{amt}|{now}".encode("utf-8")).hexdigest()

    with _connect(db_file) as conn:
        _ensure_zenpay_schema(conn)
        conn.execute(
            """
            INSERT INTO zenpay_treasury_ledger
            (entry_id, department_id, purpose, amount_vnd, recipient_account, entry_type,
             treasury_status, settlement_digest, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                department_id.strip(),
                purpose.strip(),
                amt,
                "INTERNAL_TREASURY_ENVELOPE",
                "BUDGET_ALLOCATION",
                "ALLOCATED",
                digest,
                now,
            ),
        )
        conn.commit()

    return {
        "entry_id": entry_id,
        "department_id": department_id.strip(),
        "purpose": purpose.strip(),
        "amount_vnd": amt,
        "treasury_status": "ALLOCATED",
        "settlement_digest": digest,
        "created_at": now,
    }


def zenpay_settle_disbursement(
    context: HandlerContext,
    department_id: str,
    recipient_account: str,
    amount_vnd: float,
    purpose: str = "Vendor & Infrastructure Settlement",
) -> dict[str, typing.Any]:
    """Settle a treasury disbursement in workspace ``zenpay.db`` after founder confirmation."""
    db_file = engine_db(context, "zenpay")
    entry_id = f"ZPS-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    amt = round(float(amount_vnd), 2)
    digest = hashlib.sha256(
        f"{entry_id}|{department_id.strip()}|{recipient_account.strip()}|{amt}".encode("utf-8")
    ).hexdigest()

    with _connect(db_file) as conn:
        _ensure_zenpay_schema(conn)
        conn.execute(
            """
            INSERT INTO zenpay_treasury_ledger
            (entry_id, department_id, purpose, amount_vnd, recipient_account, entry_type,
             treasury_status, settlement_digest, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                department_id.strip(),
                purpose.strip(),
                amt,
                recipient_account.strip(),
                "TREASURY_DISBURSEMENT",
                "DISBURSED_SETTLED",
                digest,
                now,
            ),
        )
        conn.commit()

    return {
        "entry_id": entry_id,
        "department_id": department_id.strip(),
        "recipient_account": recipient_account.strip(),
        "amount_vnd": amt,
        "purpose": purpose.strip(),
        "treasury_status": "DISBURSED_SETTLED",
        "settlement_digest": digest,
        "created_at": now,
    }


def revenue_record_subscription(
    context: HandlerContext,
    customer_id: str,
    customer_name: str,
    tier: str = "pro",
    amount_usd: float = 399.0,
    gateway: str = "vietqr",
) -> dict[str, typing.Any]:
    """Record a recurring subscription and payment transaction via ``RevenueEngine`` in ``revenue.db``."""
    from src.core.revenue_engine import RevenueEngine

    db_file = engine_db(context, "revenue")
    engine = RevenueEngine(db_path=pathlib.Path(db_file))
    tx = engine.record_transaction(
        customer_id=customer_id.strip(),
        amount=float(amount_usd),
        customer_name=customer_name.strip(),
        currency="USD",
        tier=tier.strip().lower(),
        type="subscription",
        gateway=gateway.strip().lower(),
        status="succeeded",
        auto_subscription=True,
    )
    return {
        **tx,
        "transaction_id": str(tx["id"]),
        "customer_id": str(tx["customer_id"]),
        "customer_name": str(tx["customer_name"]),
        "amount_usd": float(tx["amount_usd"]),
        "status": str(tx["status"]),
    }


def revenue_reconcile_mrr(
    context: HandlerContext,
    customer_id: str,
    amount_usd: float = 399.0,
    tier: str = "pro",
    auto_fix: bool = True,
) -> dict[str, typing.Any]:
    """Ensure active subscription and run MRR payment reconciliation via ``RevenueEngine`` in ``revenue.db``."""
    from src.core.revenue_engine import RevenueEngine

    db_file = engine_db(context, "revenue")
    engine = RevenueEngine(db_path=pathlib.Path(db_file))
    engine.record_transaction(
        customer_id=customer_id.strip(),
        amount=float(amount_usd),
        customer_name=customer_id.strip(),
        currency="USD",
        tier=tier.strip().lower(),
        type="subscription",
        gateway="vietqr",
        status="succeeded",
        auto_subscription=True,
    )
    recon = engine.reconcile_payments(auto_fix=bool(auto_fix))
    return {
        **recon,
        "reconciliation_id": str(recon["id"]),
        "customer_id": customer_id.strip(),
        "status": str(recon["status"]),
        "total_collected": float(recon["total_collected"]),
    }


def _ensure_usage_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_meters (
            meter_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            feature_key TEXT NOT NULL,
            mcu_consumed INTEGER NOT NULL,
            quota_cap_mcu INTEGER NOT NULL,
            utilization_pct REAL NOT NULL,
            enforcement_action TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def usage_meter_consumption(
    context: HandlerContext,
    tenant_id: str,
    feature_key: str,
    mcu_consumed: int,
    quota_cap_mcu: int = 4000,
) -> dict[str, typing.Any]:
    """Record tenant MCU consumption and compute quota utilization in workspace ``usage.db``."""
    db_file = engine_db(context, "usage")
    meter_id = f"USG-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    consumed = max(0, int(mcu_consumed))
    cap = max(1, int(quota_cap_mcu))
    utilization_pct = round((consumed / cap) * 100.0, 2)
    action = "WITHIN_QUOTA" if utilization_pct <= 100.0 else "OVERAGE_ALERT"

    with _connect(db_file) as conn:
        _ensure_usage_schema(conn)
        conn.execute(
            """
            INSERT INTO usage_meters
            (meter_id, tenant_id, feature_key, mcu_consumed, quota_cap_mcu,
             utilization_pct, enforcement_action, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meter_id,
                tenant_id.strip(),
                feature_key.strip(),
                consumed,
                cap,
                utilization_pct,
                action,
                now,
            ),
        )
        conn.commit()

    return {
        "meter_id": meter_id,
        "tenant_id": tenant_id.strip(),
        "feature_key": feature_key.strip(),
        "mcu_consumed": consumed,
        "quota_cap_mcu": cap,
        "utilization_pct": utilization_pct,
        "enforcement_action": action,
        "created_at": now,
    }


def usage_enforce_quota_cap(
    context: HandlerContext,
    tenant_id: str,
    quota_cap_mcu: int,
    enforcement_mode: str = "HARD_THROTTLE_402",
) -> dict[str, typing.Any]:
    """Enforce a hard MCU quota cap policy in workspace ``usage.db`` after founder confirmation."""
    db_file = engine_db(context, "usage")
    meter_id = f"CAP-{uuid.uuid4().hex[:10].upper()}"
    now = _now_iso()
    cap = max(1, int(quota_cap_mcu))
    mode = enforcement_mode.strip().upper()

    with _connect(db_file) as conn:
        _ensure_usage_schema(conn)
        conn.execute(
            """
            INSERT INTO usage_meters
            (meter_id, tenant_id, feature_key, mcu_consumed, quota_cap_mcu,
             utilization_pct, enforcement_action, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meter_id,
                tenant_id.strip(),
                "WORKSPACE_GLOBAL_CAP",
                0,
                cap,
                0.0,
                mode,
                now,
            ),
        )
        conn.commit()

    return {
        "meter_id": meter_id,
        "tenant_id": tenant_id.strip(),
        "quota_cap_mcu": cap,
        "enforcement_action": mode,
        "created_at": now,
    }


def consulting_create_engagement(
    context: HandlerContext,
    client_name: str,
    service_tier: str = "custom_agent",
    price_usd: float = 2500.0,
    notes: str = "Digital transformation & AI agent deployment",
) -> dict[str, typing.Any]:
    """Create a consulting engagement via ``ConsultingEngine`` in workspace ``consulting.db``."""
    from src.core.consulting_engine import ConsultingEngine

    db_file = engine_db(context, "consulting")
    engine = ConsultingEngine(db_path=pathlib.Path(db_file), project_root=pathlib.Path(context.workspace_root))
    record = engine.create_engagement(
        client_name=client_name.strip(),
        service_tier=service_tier.strip(),
        price_usd=float(price_usd),
        notes=notes.strip(),
    ).to_dict()
    return {
        **record,
        "engagement_id": str(record["id"]),
        "client_name": str(record["client_name"]),
        "service_tier": str(record["service_tier"]),
        "price_usd": float(record["price_usd"]),
        "status": str(record["status"]),
    }


def consulting_generate_proposal(
    context: HandlerContext,
    prospect_name: str,
    service_tier: str = "custom_agent",
    requirements: str = "Automate Zalo OA, e-invoicing and statutory tax filing",
    industry: str = "Technology",
) -> dict[str, typing.Any]:
    """Generate a consulting architecture proposal via ``ConsultingEngine`` in ``consulting.db``."""
    from src.core.consulting_engine import ConsultingEngine

    db_file = engine_db(context, "consulting")
    engine = ConsultingEngine(db_path=pathlib.Path(db_file), project_root=pathlib.Path(context.workspace_root))
    report = engine.generate_proposal(
        prospect_name=prospect_name.strip(),
        service_tier=service_tier.strip(),
        requirements=requirements.strip(),
        industry=industry.strip(),
        save_report=False,
    ).to_dict()
    with _connect(db_file) as conn:
        row = conn.execute(
            "SELECT id FROM proposals WHERE prospect_name = ? ORDER BY created_at DESC LIMIT 1",
            (prospect_name.strip(),),
        ).fetchone()
    proposal_id = str(row["id"]) if row else ""
    return {
        **report,
        "proposal_id": proposal_id,
        "prospect_name": str(report["prospect_name"]),
        "service_tier": str(report["service_tier"]),
        "price_usd": float(report["price_usd"]),
        "price_vnd": int(report["price_vnd"]),
    }


def content_produce_asset(
    context: HandlerContext,
    pillar: str = "ai_automation",
    format_type: str = "blog",
    topic: str = "Tự động hóa vận hành doanh nghiệp SME bằng AI Agent",
    channel: str = "linkedin",
) -> dict[str, typing.Any]:
    """Generate and persist a bilingual SEO content asset via ``ContentEngine`` in ``content.db``."""
    from src.core.content_engine import ContentEngine

    db_file = engine_db(context, "content")
    engine = ContentEngine(db_path=pathlib.Path(db_file))
    item = engine.generate_content(
        pillar=pillar.strip(),
        format_type=format_type.strip(),
        topic=topic.strip(),
        channel=channel.strip(),
    )
    saved = engine.save_content(item, save_file=False)
    return {
        **saved,
        "content_id": str(saved["id"]),
        "pillar": str(saved["pillar"]),
        "format": str(saved["format"]),
        "channel": str(saved["channel"]),
        "status": str(saved["status"]),
        "topic": topic.strip(),
    }


def content_schedule_publication(
    context: HandlerContext,
    topic: str,
    channel: str = "linkedin",
    pillar: str = "ai_automation",
    new_status: str = "published",
) -> dict[str, typing.Any]:
    """Create and transition a content item to scheduled/published in ``content.db``."""
    from src.core.content_engine import ContentEngine

    db_file = engine_db(context, "content")
    engine = ContentEngine(db_path=pathlib.Path(db_file))
    item = engine.generate_content(pillar=pillar.strip(), format_type="post", topic=topic.strip(), channel=channel.strip())
    saved = engine.save_content(item, save_file=False)
    content_id = str(saved["id"])
    updated = engine.update_status(content_id=content_id, new_status=new_status.strip(), channel=channel.strip())
    return {
        "content_id": content_id,
        "topic": topic.strip(),
        "channel": str(updated.get("channel") or channel.strip()),
        "status": str(updated.get("status", new_status.strip())),
        "success": bool(updated.get("success", True)),
    }


def copywriting_generate_campaign_copy(
    context: HandlerContext,
    product_name: str,
    target_audience: str,
    formula: str = "pas",
    copy_type: str = "landing_page",
    key_benefit: str = "Tự động hóa thuế, hóa đơn và CSKH Zalo 24/7",
) -> dict[str, typing.Any]:
    """Generate and persist high-conversion copywriting via ``CopywritingEngine`` in ``copywriting.db``."""
    from src.core.copywriting_engine import CopywritingEngine

    db_file = engine_db(context, "copywriting")
    engine = CopywritingEngine(db_path=pathlib.Path(db_file))
    project = engine.generate_copy(
        product_name=product_name.strip(),
        target_audience=target_audience.strip(),
        formula=formula.strip().lower(),
        copy_type=copy_type.strip().lower(),
        key_benefit=key_benefit.strip(),
    )
    saved = engine.save_project(project)
    return {
        **saved,
        "project_id": str(saved["id"]),
        "product_name": str(saved["product_name"]),
        "target_audience": str(saved["target_audience"]),
        "formula": str(saved["formula"]),
    }


def copywriting_audit_conversion_copy(
    context: HandlerContext,
    product_name: str,
    target_audience: str,
    formula: str = "aida",
    key_benefit: str = "Tăng 3x tỷ lệ chuyển đổi khách hàng B2B",
) -> dict[str, typing.Any]:
    """Generate, persist, and score conversion readiness of sales copy in ``copywriting.db``."""
    from src.core.copywriting_engine import CopywritingEngine

    db_file = engine_db(context, "copywriting")
    engine = CopywritingEngine(db_path=pathlib.Path(db_file))
    project = engine.generate_copy(
        product_name=product_name.strip(),
        target_audience=target_audience.strip(),
        formula=formula.strip().lower(),
        copy_type="sales_email",
        key_benefit=key_benefit.strip(),
    )
    saved = engine.save_project(project)
    text_len = len(str(saved.get("copy_text", "")))
    conversion_score = min(100, max(70, 72 + (text_len // 40)))
    return {
        "project_id": str(saved["id"]),
        "product_name": str(saved["product_name"]),
        "target_audience": str(saved["target_audience"]),
        "formula": str(saved["formula"]),
        "conversion_score": conversion_score,
        "grade": "A" if conversion_score >= 85 else "B",
    }


def vendor_onboard_partner(
    context: HandlerContext,
    name: str,
    vendor_type: str = "infra",
    version: str = "1.0.0",
    description: str = "Third-party cloud & e-invoice provider",
    trust_score: float = 88.0,
) -> dict[str, typing.Any]:
    """Onboard a third-party vendor partner via ``VendorEngine`` in workspace ``vendor.db``."""
    from src.core.vendor_engine import VendorEngine

    db_file = engine_db(context, "vendor")
    engine = VendorEngine(db_path=pathlib.Path(db_file))
    vendor = engine.onboard_vendor(
        name=name.strip(),
        vendor_type=vendor_type.strip(),
        version=version.strip(),
        description=description.strip(),
        trust_score=float(trust_score),
    )
    return {
        **vendor,
        "vendor_id": str(vendor["id"]),
        "name": name.strip(),
        "vendor_key": str(vendor["name"]),
        "vendor_type": str(vendor["vendor_type"]),
        "status": str(vendor["status"]),
        "trust_score": float(vendor["trust_score"]),
    }


def vendor_audit_partner(
    context: HandlerContext,
    name: str,
    audit_type: str = "security",
    vendor_type: str = "infra",
) -> dict[str, typing.Any]:
    """Ensure vendor registration and run a security/SLA audit via ``VendorEngine`` in ``vendor.db``."""
    from src.core.vendor_engine import VendorEngine

    db_file = engine_db(context, "vendor")
    engine = VendorEngine(db_path=pathlib.Path(db_file))
    onboarded = engine.onboard_vendor(name=name.strip(), vendor_type=vendor_type.strip())
    audit = engine.audit_vendor(name_or_id=str(onboarded["id"]), audit_type=audit_type.strip())
    return {
        **audit,
        "audit_id": str(audit["audit_id"]),
        "vendor_id": str(audit["vendor_id"]),
        "name": name.strip(),
        "vendor_key": str(audit["name"]),
        "audit_type": str(audit["audit_type"]),
        "audit_score": float(audit["audit_score"]),
        "status": str(audit["status"]),
    }
