# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""AgentKit Multi-Kit Registry & Multi-Target Exporter.

Implements the AgentKit architecture (https://agentkit.best/docs):
- 4 Canonical Kits:
    1. kit:re        — Reverse Engineering, Binary/APK/Web Analysis & Security Audit
    2. kit:engineer  — SDLC, Code, Deploy, Doctor, Sandbox, Harness & PEV
    3. kit:business  — Vietnam Tax (Thuế), Accounting (Kế toán), Legal & Operations
    4. kit:marketing — Zalo OA, Sophia Video Factory, Content & Growth Funnels
- 7 Native Agent Targets + Portable:
    claude-code, codex, cursor, agy, pi, omp, dsh, portable
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from src.core.kit_storage import OwnershipLedger, SCHEMA_VERSION

SUPPORTED_TARGETS: tuple[str, ...] = (
    "claude-code",
    "codex",
    "cursor",
    "agy",
    "pi",
    "omp",
    "dsh",
    "portable",
)


@dataclass(frozen=True)
class KitDefinition:
    """Descriptor for an AgentKit modular kit."""

    id: str
    name: str
    description: str
    version: str = "6.0.0"
    commands: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)
    panel_title: str = ""


CANONICAL_KITS: Dict[str, KitDefinition] = {
    "kit:re": KitDefinition(
        id="kit:re",
        name="Mekong Reverse Engineering Kit",
        description="Agentic Reverse Engineering (Web/SaaS RES, Ghidra/r2/JADX MCP, Static & Dynamic Audit)",
        commands=["re", "cyber", "forensic", "security"],
        skills=["re-web", "re-binary", "re-apk", "re-protocol", "re-codebase-audit"],
        mcp_servers=["ghidra", "radare2", "jadx", "chrome-devtools"],
        panel_title="Kit: Reverse Engineering (kit:re)",
    ),
    "kit:engineer": KitDefinition(
        id="kit:engineer",
        name="Mekong Engineer & SDLC Kit",
        description="Full-stack SDLC, PEV Harness, Doctor Diagnostics, Worktree, Code & Deploy Suite",
        commands=["cook", "plan", "build", "code", "deploy", "doctor", "pev", "sandbox", "worktree", "ship", "kit"],
        skills=["ak-plan", "ak-cook", "ak-fix", "ak-ship", "ak-doctor"],
        mcp_servers=["filesystem", "git"],
        panel_title="Kit: Engineer & SDLC (kit:engineer)",
    ),
    "kit:business": KitDefinition(
        id="kit:business",
        name="Mekong Business & Vietnam Compliance Kit",
        description="Vietnam Tax (TNCN/TNDN/GTGT), TT78 Accounting, Enterprise Law & Operations",
        commands=["thue", "ke-toan", "company", "billing", "ops", "revenue", "consulting", "enterprise", "taxadmin"],
        skills=["vn-tax-tncn", "vn-tax-tndn", "vn-accounting-tt78", "company-blueprint"],
        mcp_servers=["d1-database", "polar-billing"],
        panel_title="Kit: Business & Compliance (kit:business)",
    ),
    "kit:marketing": KitDefinition(
        id="kit:marketing",
        name="Mekong Marketing & Growth Funnel Kit",
        description="Zalo OA Automation, Sophia AI Video Factory, Bilingual Copywriting & Sales Funnels",
        commands=["zalo-oa", "sophia", "marketing", "sales", "content", "copywriting", "ui"],
        skills=["zalo-oa-campaign", "sophia-video-pipeline", "bilingual-copywriter"],
        mcp_servers=["zalo-oa", "sophia-render"],
        panel_title="Kit: Marketing & Growth (kit:marketing)",
    ),
}


class KitRegistry:
    """Registry managing the 4 canonical Kits and multi-target exports."""

    def __init__(self) -> None:
        self._kits: Dict[str, KitDefinition] = dict(CANONICAL_KITS)

    def list_kits(self) -> List[KitDefinition]:
        """Return all registered kits in deterministic order."""
        return [self._kits[k] for k in ("kit:re", "kit:engineer", "kit:business", "kit:marketing") if k in self._kits]

    def get_kit(self, kit_id: str) -> KitDefinition | None:
        """Lookup kit by ID (accepts 're' or 'kit:re')."""
        normalized = kit_id if kit_id.startswith("kit:") else f"kit:{kit_id}"
        return self._kits.get(normalized)

    def render_target_manifest(self, kit: KitDefinition, target: str) -> Dict[str, Any]:
        """Generate target-specific manifest dictionary for an agent runtime."""
        if target not in SUPPORTED_TARGETS:
            raise ValueError(f"Unsupported target '{target}'. Must be one of: {', '.join(SUPPORTED_TARGETS)}")

        base = {
            "schema": SCHEMA_VERSION,
            "kit_id": kit.id,
            "name": kit.name,
            "version": kit.version,
            "target": target,
            "description": kit.description,
            "commands": kit.commands,
            "skills": kit.skills,
            "mcp_servers": kit.mcp_servers,
        }

        if target == "claude-code":
            base["entrypoint"] = f"mekong --kit {kit.id}"
            base["slash_commands"] = [f"/mk-{cmd}" for cmd in kit.commands]
        elif target == "cursor":
            base["rules_format"] = "mdc"
            base["globs"] = ["src/**/*.py", "tests/**/*.py"]
        elif target == "codex":
            base["sandbox_mode"] = "workspace-write"
        elif target == "agy":
            base["governance_mode"] = "strict-3-tier"
        elif target in ("pi", "omp", "dsh"):
            base["agent_protocol"] = target
        elif target == "portable":
            base["portable_bundle"] = True

        return base

    def export_kit(
        self,
        kit_id: str,
        target: str,
        output_dir: Path,
        record_ownership: bool = True,
    ) -> Path:
        """Export a kit manifest for the given target and track SHA-256 in ownership.json."""
        kit = self.get_kit(kit_id)
        if kit is None:
            raise KeyError(f"Unknown kit '{kit_id}'. Available: {', '.join(self._kits.keys())}")
        if target not in SUPPORTED_TARGETS:
            raise ValueError(f"Unsupported target '{target}'. Supported: {', '.join(SUPPORTED_TARGETS)}")

        manifest = self.render_target_manifest(kit, target)
        short_id = kit.id.replace("kit:", "")
        target_dir = output_dir / target
        target_dir.mkdir(parents=True, exist_ok=True)
        out_file = target_dir / f"kit-{short_id}.json"
        out_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        if record_ownership:
            ledger = OwnershipLedger(root_dir=output_dir)
            try:
                rel_path = out_file.resolve().relative_to(output_dir.resolve()).as_posix()
                ledger.register_file(rel_path, owner=kit.id)
            except ValueError:
                pass

        return out_file


__all__ = [
    "SUPPORTED_TARGETS",
    "KitDefinition",
    "CANONICAL_KITS",
    "KitRegistry",
]
