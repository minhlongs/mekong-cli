"""Deep Brainstorm Contract & Option Synthesis for 25-Step Open-Core + SaaS (Phase 561)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from src.core.opencore.phase_559_opencore_25_step_catalog import OpenCorePhase
from src.core.opencore.phase_560_opencore_saas_readiness_engine import (
    OpenCoreSaasReadinessEngine,
)


@dataclass(frozen=True)
class BrainstormContract:
    outcome: str
    constraints: tuple[str, ...]
    non_goals: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]


@dataclass(frozen=True)
class BrainstormOption:
    option_id: str
    title: str
    summary: str
    pros: tuple[str, ...]
    cons: tuple[str, ...]
    recommended: bool


@dataclass(frozen=True)
class DeepIdeaBrainstormReport:
    idea_text: str
    deep_mode: bool
    stage: str
    archetype: str
    contract: BrainstormContract
    options: tuple[BrainstormOption, ...]
    recommended_option_id: str
    tri_layer: dict[str, str]
    phases_summary: dict[str, list[dict[str, Any]]]
    readiness_verdict: str
    safe_for_public_github: bool
    saas_paywall_active: bool
    contract_digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OpenCoreDeepBrainstormEngine:
    """Synthesizes a bounded brainstorm contract and 25-step Open-Core + SaaS architecture."""

    @staticmethod
    def build_contract(idea_text: str) -> BrainstormContract:
        return BrainstormContract(
            outcome=(
                f"Public GitHub MIT Open-Core repository with active Cloud SaaS monetization "
                f"across 25 verified steps for: {idea_text.strip()}"
            ),
            constraints=(
                "Strictly <= 185 LOC per Python module; zero vendor SDK imports in src/core/",
                "Zero leaked secrets in Git history or .env.example; apps/ and billing/ quarantined",
                "Zero synthetic revenue event pollution in .mekong/company.json",
                "Preserve 100% compatibility with existing CLI groups and core boundary tests",
            ),
            non_goals=(
                "Do not expose proprietary tenant apps/ or internal billing/ code to public git index",
                "Do not fabricate customer revenue or synthetic billing events as traction",
                "Do not replace MIT license on public core runtime modules",
            ),
            acceptance_criteria=(
                "All 25 Open-Core steps mapped across 5 phases with OSS vs. SaaS boundaries",
                "OpenCoreSaasReadinessEngine verdict == PUBLIC_GITHUB_SAAS_READY",
                "FastAPI JWT license_gate + MCUBilling HTTP 402 + PayOS/NOWPayments IPN verified",
                "CLI `mekong idea run ... --deep` and `mekong opencore-saas brainstorm --deep` pass 100%",
            ),
        )

    @staticmethod
    def compare_options() -> tuple[BrainstormOption, ...]:
        return (
            BrainstormOption(
                option_id="A",
                title="25-Step Open-Core (MIT Public Core + Hosted Control Plane & MCU SaaS)",
                summary="Publish stdlib-pure MIT core/CLI on GitHub; monetize cloud gateway, JWT tiers, MCU credits, and VietQR/PayOS webhooks.",
                pros=("Max developer adoption & PLG trust", "Recurring SaaS/RaaS revenue via HTTP 402 + JWT tiers", "Clean IP quarantine"),
                cons=("Requires strict CI leak & boundary gates"),
                recommended=True,
            ),
            BrainstormOption(
                option_id="B",
                title="Pure Open-Source Monorepo (100% MIT + Sponsorships)",
                summary="Release entire stack including billing and dashboards under MIT; rely on donations or consulting.",
                pros=("Zero license boundary maintenance"),
                cons=("No recurring SaaS paywall moat", "Exposes proprietary tenant workflows"),
                recommended=False,
            ),
            BrainstormOption(
                option_id="C",
                title="Closed-Source Proprietary SaaS Only",
                summary="Keep all CLI and runtime code private; sell only hosted seat licenses.",
                pros=("Simple IP control"),
                cons=("Loses GitHub developer distribution & BYOK local-first trust", "High CAC"),
                recommended=False,
            ),
        )

    @classmethod
    def synthesize(
        cls,
        idea_text: str,
        repo_root: str | Path = ".",
        deep: bool = True,
    ) -> DeepIdeaBrainstormReport:
        audit = OpenCoreSaasReadinessEngine.audit_repository(Path(repo_root))
        phases_map: dict[str, list[dict[str, Any]]] = {}
        for phase in OpenCorePhase:
            steps = OpenCoreSaasReadinessEngine.list_steps(phase)
            phases_map[phase.value] = [
                {
                    "step": s.step_number,
                    "slug": s.slug,
                    "oss_public": s.oss_public_surface,
                    "saas_monetized": s.saas_monetized_surface,
                }
                for s in steps
            ]
        contract = cls.build_contract(idea_text)
        digest_payload = json.dumps(
            {"contract": asdict(contract), "phases": phases_map, "verdict": audit.verdict.value},
            sort_keys=True,
            ensure_ascii=False,
        )
        digest = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
        return DeepIdeaBrainstormReport(
            idea_text=idea_text,
            deep_mode=deep,
            stage="zero",
            archetype="Open-Core MIT + Cloud SaaS/RaaS (B2B/Solo-Founder)",
            contract=contract,
            options=cls.compare_options(),
            recommended_option_id="A",
            tri_layer={
                "Business": "MIT CLI drives zero-CAC PLG funnel; Cloud Control Plane monetizes via BASIC/PREMIUM/ENTERPRISE/MASTER & MCU top-ups.",
                "Agentic": "Local BYOK agents run in fail-closed sandbox; SaaS tier unlocks 24/7 daemon, multi-region queues, and verified recipe marketplace.",
                "Governance": "Zero leaked keys, apps/ & billing/ gitignored, SHA-256 AuditLedger (TT78/SOC2), CLA & Trademark protection.",
            },
            phases_summary=phases_map,
            readiness_verdict=audit.verdict.value,
            safe_for_public_github=audit.safe_for_public_github_push,
            saas_paywall_active=audit.saas_paywall_active,
            contract_digest=digest,
        )
