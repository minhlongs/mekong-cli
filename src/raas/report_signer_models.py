# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and hash chain helpers for ReportSigner."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, List, Optional


@dataclass
class SignatureResult:
    """Result of signing operation."""

    signature: str
    hash_value: str
    timestamp: str
    key_id: str


@dataclass
class VerificationResult:
    """Result of signature verification."""

    valid: bool
    hash_match: bool = True
    timestamp: str = ""
    error: Optional[str] = None


def compute_hash_chain_events(
    events: List[Dict[str, Any]],
    previous_hash: str = "0" * 64,
) -> str:
    """Compute SHA-256 hash chain for an event sequence."""
    sorted_events = sorted(
        events,
        key=lambda e: e.get(
            "occurred_at", e.get("created_at", e.get("validated_at", ""))
        ),
    )

    hasher = hashlib.sha256()
    hasher.update(previous_hash.encode())

    for event in sorted_events:
        event_json = json.dumps(event, sort_keys=True)
        hasher.update(event_json.encode())

    return hasher.hexdigest()


__all__ = [
    "SignatureResult",
    "VerificationResult",
    "compute_hash_chain_events",
]
