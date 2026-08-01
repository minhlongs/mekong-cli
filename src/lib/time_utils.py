"""UTC timestamp helpers shared by CLI automation paths."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_iso_now() -> str:
    """Return current UTC time as ISO-8601 with trailing Z."""
    return utc_now().isoformat().replace("+00:00", "Z")


def utc_iso_after(days: int) -> str:
    """Return UTC ISO-8601 timestamp after a number of days."""
    return (utc_now() + timedelta(days=days)).isoformat().replace("+00:00", "Z")


__all__ = ["utc_iso_after", "utc_iso_now", "utc_now"]
