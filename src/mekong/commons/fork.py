"""fork.py — Right-to-Fork executor for ZenOS Commons.

ZENOS Art 8 guarantees every member or particle data sovereignty on exit.
This module implements the协议-level guarantee as a self-contained JSON
export plus a companion Git clone instruction.

Invocation: `mekong commons fork` via the `/mk:govern fork` command (F3 CLI).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ForkExport:
    bundle_version: str = "zenos-fork-v1"
    exported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notice_period_days: int = 30
    exported_by: str = ""
    constitution_commit: str = ""
    manifest_hash: str = ""

    # Bundled artifacts (populated by ForkExecutor)
    member_list: list[dict] = field(default_factory=list)
    voting_history: list[dict] = field(default_factory=list)
    treasury_snapshot: dict = field(default_factory=dict)
    behavior_graph_subgraph: dict = field(default_factory=dict)
    constitution_text: str = ""
    export_instructions: str = ""

    def compute_hash(self) -> str:
        payload = json.dumps(
            {
                "exported_at": self.exported_at.isoformat(),
                "members": self.member_list,
                "proposals": self.voting_history,
                "treasury": self.treasury_snapshot,
                "constitution_commit": self.constitution_commit,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()


class ForkError(Exception):
    pass


class NoticePeriodError(ForkError):
    pass


class ExportPathError(ForkError):
    pass


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


@dataclass
class ForkExecutor:
    """Produce a self-contained fork bundle."""

    repo_root: Path = field(default_factory=lambda: Path(".").resolve())
    constitution_path: Path = field(default_factory=lambda: Path("mekong/constitution/ZENOS.md"))
    default_notice_days: int = 30
    bundle_version: str = "zenos-fork-v1"

    def validate_notice_period(self, member_joined_at: datetime, *, at: Optional[datetime] = None) -> int:
        """Return days remaining until the 30-day notice period is satisfied.

        Raises `NoticePeriodError` if the member has not yet served 30 days.
        """
        w = at or datetime.now(timezone.utc)
        elapsed = (w - member_joined_at).total_seconds() / 86400.0
        remaining = self.default_notice_days - elapsed
        if remaining > 0:
            raise NoticePeriodError(
                f"Notice period not satisfied: {remaining:.1f} days remaining "
                f"(joined {member_joined_at.date()}, need 30 days)"
            )
        return max(0, int(remaining))

    def compute_constitution_commit(self) -> str:
        path = self.repo_root / self.constitution_path
        if not path.exists():
            return ""
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "HEAD:{}".format(str(self.constitution_path))],
                cwd=str(self.repo_root),
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            return out[:12]
        except subprocess.CalledProcessError:
            # Non-git or file not in HEAD — return empty marker.
            return ""

    def build_bundle(
        self,
        *,
        exported_by: str,
        member_list: list[dict],
        voting_history: list[dict],
        treasury_snapshot: dict,
        behavior_graph_subgraph: Optional[dict] = None,
        constitution_text: str = "",
    ) -> ForkExport:
        commit = self.compute_constitution_commit()
        bundle = ForkExport(
            exported_by=exported_by,
            constitution_commit=commit,
            member_list=list(member_list),
            voting_history=list(voting_history),
            treasury_snapshot=dict(treasury_snapshot),
            behavior_graph_subgraph=behavior_graph_subgraph or {},
            constitution_text=constitution_text,
            export_instructions=self._instructions(),
        )
        bundle.manifest_hash = bundle.compute_hash()
        return bundle

    def write_bundle(self, bundle: ForkExport, dest: Path) -> Path:
        dest = Path(dest)
        dest.mkdir(parents=True, exist_ok=True)
        out_file = dest / f"fork-export-{bundle.exported_at.strftime('%Y%m%dT%H%M%SZ')}.json"
        payload = self._serialize(bundle)
        out_file.write_text(payload, encoding="utf-8")
        return out_file

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _instructions(self) -> str:
        commit = self.compute_constitution_commit()
        return "\n".join([
            "## ZenOS Fork Export Instructions",
            "",
            "1. Clone this repository:",
            "   git clone <REPO_URL> my-fork",
            "",
            "2. The export manifest was produced at commit:",
            f"   {commit}",
            "",
            "3. Load `manifest.json` (or the per-timestamp export file) to restore:",
            "   - member_list → your member registry",
            "   - voting_history → your amendment audit trail",
            "   - treasury_snapshot → your ledger state",
            "   - behavior_graph_subgraph → your trust network state",
            "",
            "4. The protocol license is MIT at the fork commit.",
            "",
            "5. Exit guarantee per ZENOS Art 8: no lock-in, no penalty, no "
            "proprietary format traps.",
        ])

    def _serialize(self, bundle: ForkExport) -> str:
        data = {
            "bundle_version": bundle.bundle_version,
            "exported_at": bundle.exported_at.isoformat(),
            "notice_period_days": bundle.notice_period_days,
            "exported_by": bundle.exported_by,
            "constitution_commit": bundle.constitution_commit,
            "manifest_hash": bundle.manifest_hash,
            "member_list": bundle.member_list,
            "voting_history": bundle.voting_history,
            "treasury_snapshot": bundle.treasury_snapshot,
            "behavior_graph_subgraph": bundle.behavior_graph_subgraph,
            "constitution_text": bundle.constitution_text,
            "export_instructions": bundle.export_instructions,
        }
        return json.dumps(data, indent=2, sort_keys=True, default=str)
