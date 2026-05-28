"""Regex policy router — decide local vs cloud per request."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal

from mekongd.config import PolicyConfig
from mekongd.schemas import MessagesRequest

log = logging.getLogger(__name__)

Destination = Literal["local", "cloud"]


@dataclass
class RouteDecision:
    destination: Destination
    reason: str


class Router:
    """Match system prompt (or first user message) against regex policies."""

    def __init__(self, policy: PolicyConfig):
        self.policy = policy
        self._local_re = [re.compile(p) for p in policy.local_patterns]
        self._cloud_re = [re.compile(p) for p in policy.cloud_patterns]

    def decide(self, request: MessagesRequest) -> RouteDecision:
        text = self._extract_text(request)
        # Cloud patterns take precedence — high-stakes work must not downgrade.
        for pat in self._cloud_re:
            if pat.search(text):
                return RouteDecision(destination="cloud", reason=f"cloud pattern: {pat.pattern!r}")
        for pat in self._local_re:
            if pat.search(text):
                return RouteDecision(destination="local", reason=f"local pattern: {pat.pattern!r}")
        return RouteDecision(
            destination=self.policy.default_destination,  # type: ignore[arg-type]
            reason=f"default: {self.policy.default_destination}",
        )

    @staticmethod
    def _extract_text(request: MessagesRequest) -> str:
        parts: list[str] = []
        system_text = request.get_system_text()
        if system_text:
            parts.append(system_text)
        if request.messages:
            first = request.messages[0]
            if isinstance(first.content, str):
                parts.append(first.content)
            else:
                parts.extend(cb.text for cb in first.content)
        return "\n".join(parts)
