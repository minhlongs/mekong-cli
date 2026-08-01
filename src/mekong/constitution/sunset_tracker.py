"""sunset_tracker.py — Track constitutional sunset clauses and expiry alerts.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from src.mekong.constitution.commons_parser import CommonsConfig


class SunSetTrackerError(Exception):
    pass


@dataclass(frozen=True)
class ArticleExpiry:
    """Per-article expiry metadata."""
    label: str
    expires_at: Optional[datetime]
    context: str = ""


@dataclass(frozen=True)
class SunSetReport:
    config: CommonsConfig
    generated_at: datetime
    charter_expires_at: Optional[datetime]
    years_left: Optional[float]
    article_expiries: list[ArticleExpiry]
    alerts: list[str] = field(default_factory=list)
    needs_reratification: bool = False

    def is_imminent(self, *, years: float = 2.0) -> bool:
        if self.years_left is None:
            return False
        return self.years_left <= years

    def summarize(self) -> str:
        lines = [
            f"SunSet report — {self.generated_at.date()}",
            f"Charter version: {self.config.version}",
        ]
        if self.charter_expires_at:
            lines.append(
                f"Charter expiry: {self.charter_expires_at.date()} "
                f"({self.years_left:.1f} years remaining)"
            )
        else:
            lines.append("Charter expiry: not set")
        if self.article_expiries:
            lines.append("Per-article expiries:")
            for a in self.article_expiries:
                when = a.expires_at.date() if a.expires_at else "none"
                lines.append(f"  - {a.label}: {when}")
        if self.alerts:
            lines.append("Alerts:")
            for msg in self.alerts:
                lines.append(f"  - {msg}")
        if self.needs_reratification:
            lines.append("ACTION REQUIRED: charter re-ratification due")
        return "\n".join(lines)


@dataclass
class SunSetTracker:
    """Compute expiry alerts from a parsed CommonsConfig."""
    charter_created_at: Optional[datetime] = None
    logger: Optional[Callable[[str], None]] = None

    def build_report(self, config: CommonsConfig, *, at: Optional[datetime] = None) -> SunSetReport:
        w = at or datetime.now(timezone.utc)
        created = self.charter_created_at
        if created is None:
            created = self._source_mtime(config.source)
        expires = self._add_years(created, config.sunset_years) if created else None
        years_left = ((expires - w).total_seconds() / 86400 / 365.25) if expires else None
        alerts: list[str] = []
        needs_reratification = False
        if years_left is not None:
            if years_left <= 0:
                alerts.append(
                    f"Charter expired {abs(years_left):.1f} years ago — "
                    "requires 4/5 supermajority re-ratification per ZENOS Art 9"
                )
                needs_reratification = True
            elif years_left <= 2:
                alerts.append(f"Charter expires in {years_left:.1f} years — begin re-ratification planning")
        report = SunSetReport(
            config=config,
            generated_at=w,
            charter_expires_at=expires,
            years_left=years_left,
            article_expiries=[],
            alerts=alerts,
            needs_reratification=needs_reratification,
        )
        if self.logger:
            self.logger(report.summarize())
        return report

    def _source_mtime(self, source: str) -> Optional[datetime]:
        try:
            p = Path(source)
            if p.exists():
                return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        except Exception:
            pass
        return None

    @staticmethod
    def _add_years(dt: datetime, years: int) -> datetime:
        try:
            return dt.replace(year=dt.year + years)
        except ValueError:
            try:
                return dt.replace(month=3, day=1, year=dt.year + years)
            except Exception:
                return dt.replace(year=dt.year + years, month=3, day=1)
