# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Cryptographically verifiable, SHA-256 hash-chained immutable audit ledger."""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import pathlib
import threading
import typing

GENESIS_HASH = "0" * 64


@dataclasses.dataclass(frozen=True)
class AuditEntry:
    index: int
    timestamp: str
    event_type: str
    actor: str
    payload: dict[str, typing.Any]
    previous_hash: str
    hash: str

    def to_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


def compute_entry_hash(
    index: int,
    timestamp: str,
    event_type: str,
    actor: str,
    payload: dict[str, typing.Any],
    previous_hash: str,
) -> str:
    canonical_payload = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    raw = f"{index}:{timestamp}:{event_type}:{actor}:{canonical_payload}:{previous_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AuditLedger:
    """Thread-safe, append-only, SHA-256 hash-chained compliance audit ledger."""

    def __init__(self, ledger_file: str | pathlib.Path | None = None) -> None:
        if ledger_file is None:
            base_dir = pathlib.Path(".mekong") / "ledger"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.ledger_file = base_dir / "audit_chain.jsonl"
        else:
            self.ledger_file = pathlib.Path(ledger_file)
            self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._last_hash: str = GENESIS_HASH
        self._count: int = 0
        self._replay_existing()

    def _replay_existing(self) -> None:
        if not self.ledger_file.exists():
            return
        with self.ledger_file.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                data = json.loads(stripped)
                self._last_hash = data.get("hash", GENESIS_HASH)
                self._count += 1

    def append_event(
        self,
        event_type: str,
        actor: str,
        payload: dict[str, typing.Any],
    ) -> AuditEntry:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._lock:
            index = self._count
            prev_hash = self._last_hash
            entry_hash = compute_entry_hash(
                index=index,
                timestamp=now_iso,
                event_type=event_type,
                actor=actor,
                payload=payload,
                previous_hash=prev_hash,
            )
            entry = AuditEntry(
                index=index,
                timestamp=now_iso,
                event_type=event_type,
                actor=actor,
                payload=payload,
                previous_hash=prev_hash,
                hash=entry_hash,
            )
            with self.ledger_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
            self._last_hash = entry_hash
            self._count += 1
            return entry

    def get_entries(self) -> list[AuditEntry]:
        entries: list[AuditEntry] = []
        if not self.ledger_file.exists():
            return entries
        with self.ledger_file.open("r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                d = json.loads(line_str)
                entries.append(
                    AuditEntry(
                        index=d["index"],
                        timestamp=d["timestamp"],
                        event_type=d["event_type"],
                        actor=d["actor"],
                        payload=d["payload"],
                        previous_hash=d["previous_hash"],
                        hash=d["hash"],
                    )
                )
        return entries

    def verify_integrity(self) -> bool:
        with self._lock:
            entries = self.get_entries()
            expected_prev = GENESIS_HASH
            for e in entries:
                if e.previous_hash != expected_prev:
                    return False
                calc_hash = compute_entry_hash(
                    index=e.index,
                    timestamp=e.timestamp,
                    event_type=e.event_type,
                    actor=e.actor,
                    payload=e.payload,
                    previous_hash=e.previous_hash,
                )
                if e.hash != calc_hash:
                    return False
                expected_prev = e.hash
            return True


__all__ = ["GENESIS_HASH", "AuditEntry", "AuditLedger", "compute_entry_hash"]
