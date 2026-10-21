# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Outcome Recorder Analysis and Patterns Mixin."""

from __future__ import annotations

from typing import Any

from src.learning.outcome_models import ExecutionOutcome, OutcomeStatus


class OutcomeRecorderAnalysisMixin:
    """Mixin for querying similar failures, failure patterns, and auto-tuning."""

    _bridge: Any | None
    _outcome_index: list[ExecutionOutcome]

    def _get_bridge(self) -> Any:
        raise NotImplementedError

    def find_similar_failures(
        self,
        *,
        error_type: str | None = None,
        provider: str | None = None,
        command: str | None = None,
        limit: int = 10,
    ) -> list[ExecutionOutcome]:
        from src.core.memory_bridge import MemoryKind

        outcomes: list[ExecutionOutcome] = []
        try:
            bridge = self._bridge or self._get_bridge()
            query_parts: list[str] = []
            if error_type:
                query_parts.append(error_type)
            if provider:
                query_parts.append(provider)
            if command:
                token = command.split()[0] if command else ""
                if token:
                    query_parts.append(token)
            query = " ".join(query_parts) if query_parts else "failure error"
            results = bridge.search(query=query, limit=limit, kind=MemoryKind.EPISODIC)
            for rec in results:
                meta = rec.metadata or {}
                if meta.get("status") != OutcomeStatus.FAILURE.value:
                    continue
                if error_type and meta.get("error_type") != error_type:
                    continue
                if provider and meta.get("provider") != provider:
                    continue
                if command and command not in (meta.get("command") or ""):
                    continue
                try:
                    outcomes.append(ExecutionOutcome.from_dict(meta))
                except (KeyError, ValueError):
                    continue
        except Exception:
            pass

        if not outcomes:
            for o in self._outcome_index:
                if o.status != OutcomeStatus.FAILURE:
                    continue
                if error_type and o.error_type != error_type:
                    continue
                if provider and o.provider != provider:
                    continue
                if command and command not in (o.command or ""):
                    continue
                outcomes.append(o)

        outcomes.sort(key=lambda o: o.finished_at, reverse=True)
        return outcomes[:limit]

    def get_failure_patterns(self, min_occurrences: int = 3) -> list[dict[str, Any]]:
        groups: dict[tuple[str | None, str | None], list[ExecutionOutcome]] = {}
        for o in self._outcome_index:
            if o.status != OutcomeStatus.FAILURE:
                continue
            key = (o.error_type, o.provider)
            groups.setdefault(key, []).append(o)

        patterns: list[dict[str, Any]] = []
        for (error_type, provider), items in groups.items():
            if len(items) < min_occurrences:
                continue
            items.sort(key=lambda o: o.finished_at, reverse=True)
            commands = list({o.command for o in items if o.command})[:5]
            patterns.append({
                "error_type": error_type or "unknown",
                "provider": provider or "unknown",
                "occurrences": len(items),
                "sample_commands": commands,
                "last_seen": items[0].finished_at,
                "suggested_action": self._suggest_action(error_type, provider),
            })
        patterns.sort(key=lambda p: p["occurrences"], reverse=True)
        return patterns

    @staticmethod
    def _suggest_action(error_type: str | None, provider: str | None) -> str:
        suggestions = {
            "timeout": "Increase timeout or switch provider",
            "auth": "Check API key / credentials",
            "rate_limit": "Add delay between retries",
            "connection": "Check network / try fallback provider",
            "invalid_api_key": "Rotate API key",
            "forbidden": "Check permissions / quota",
            "context_length": "Reduce prompt size or use longer-context model",
        }
        key = (error_type or "").lower().split(":")[0]
        return suggestions.get(key, "Review error and consider alternative provider")

    def suggest_retry_threshold(
        self,
        *,
        error_type: str | None = None,
        provider: str | None = None,
        current_threshold: int = 3,
        max_threshold: int = 5,
    ) -> int:
        similar = self.find_similar_failures(error_type=error_type, provider=provider, limit=50)
        if not similar:
            return current_threshold
        avg_retries = sum(o.retry_count for o in similar) / len(similar)
        if avg_retries >= current_threshold:
            return min(current_threshold + 1, max_threshold)
        if avg_retries < current_threshold * 0.4:
            return max(current_threshold - 1, 1)
        return current_threshold
