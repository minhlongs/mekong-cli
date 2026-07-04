"""Multi-scope memory tagging for agent isolation.

Prevents inter-agent state corruption by scoping every memory entry to a
deterministic (app, org, user, agent, session) tuple and enforcing read/write
rules at the store boundary.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MemoryScope:
    """Hierarchical scope identifier for a memory entry."""

    app_id: str = "mekong"
    org_id: str | None = None
    user_id: str | None = None
    agent_id: str | None = None
    session_id: str | None = None


@dataclass
class ScopedMemoryEntry:
    """A single memory value bound to a scope."""

    key: str
    value: Any
    scope: MemoryScope
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    ttl: int | None = None  # seconds; None = permanent

    def is_expired(self) -> bool:
        """Return True if entry has exceeded its TTL."""
        if self.ttl is None:
            return False
        return time.time() > self.created_at + self.ttl


def validate_access(requestor: MemoryScope, target: MemoryScope) -> bool:
    """Enforce read rules between requestor and target scope.

    Rules:
    - app_id must match.
    - If target has an org_id, requestor must share it.
    - If target has a user_id, requestor must share it.
    - If target has an agent_id (agent-private entry), requestor must share
      that agent_id. agent_id=None on target means the entry is shared and
      readable by any agent within the same org/user scope.
    """
    if requestor.app_id != target.app_id:
        return False
    if target.org_id is not None and requestor.org_id != target.org_id:
        return False
    if target.user_id is not None and requestor.user_id != target.user_id:
        return False
    if target.agent_id is not None and requestor.agent_id != target.agent_id:
        return False
    return True


class ScopedMemoryStore:
    """In-memory key-value store with multi-scope isolation."""

    def __init__(self) -> None:
        # keyed by (scope_key, entry_key)
        self._store: dict[tuple[str, str], ScopedMemoryEntry] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, entry: ScopedMemoryEntry) -> None:
        """Persist or overwrite an entry.

        Preserves original created_at on overwrite; bumps updated_at.
        """
        composite = (self._scope_key(entry.scope), entry.key)
        existing = self._store.get(composite)
        if existing is not None:
            entry.created_at = existing.created_at
        entry.updated_at = time.time()
        self._store[composite] = entry
        logger.debug("stored key=%s scope=%s", entry.key, composite[0])

    def retrieve(self, key: str, scope: MemoryScope) -> ScopedMemoryEntry | None:
        """Return entry if it exists, is accessible, and has not expired.

        First checks the exact scope key (fast path), then falls back to a
        linear scan for shared entries stored under a different scope key
        (e.g. agent_id=None entries looked up by an agent-scoped requestor).
        """
        composite = (self._scope_key(scope), key)
        entry = self._store.get(composite)
        if entry is not None:
            if entry.is_expired():
                del self._store[composite]
                return None
            if validate_access(scope, entry.scope):
                return entry

        # Fallback: scan for accessible entries with the same key stored
        # under a different scope key (shared / parent-scope entries).
        for stored_composite, stored_entry in list(self._store.items()):
            if stored_composite[1] != key:
                continue
            if stored_composite == composite:
                continue  # already checked above
            if stored_entry.is_expired():
                del self._store[stored_composite]
                continue
            if validate_access(scope, stored_entry.scope):
                return stored_entry

        logger.debug("retrieve miss: key=%s scope=%s", key, self._scope_key(scope))
        return None

    def query(self, scope: MemoryScope) -> list[ScopedMemoryEntry]:
        """Return all non-expired entries accessible to *scope*.

        Includes entries where agent_id is None (shared) as well as entries
        owned by the same agent.
        """
        results: list[ScopedMemoryEntry] = []
        for entry in list(self._store.values()):
            if entry.is_expired():
                continue
            if validate_access(scope, entry.scope):
                results.append(entry)
        return results

    def delete(self, key: str, scope: MemoryScope) -> bool:
        """Remove entry; returns True if found and deleted."""
        composite = (self._scope_key(scope), key)
        if composite in self._store:
            del self._store[composite]
            logger.debug("deleted key=%s scope=%s", key, composite[0])
            return True
        return False

    def prune_expired(self) -> int:
        """Remove all TTL-expired entries; return count removed."""
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired:
            del self._store[k]
        if expired:
            logger.info("pruned %d expired entries", len(expired))
        return len(expired)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _scope_key(scope: MemoryScope) -> str:
        """Deterministic string representation of a scope."""
        parts = [
            scope.app_id,
            scope.org_id or "",
            scope.user_id or "",
            scope.agent_id or "",
            scope.session_id or "",
        ]
        return "|".join(parts)
