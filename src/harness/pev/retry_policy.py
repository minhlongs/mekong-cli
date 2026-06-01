"""Stub: retry policy for PEV orchestrator."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_factor: float = 2.0
    initial_delay_secs: float = 1.0
    max_delay_secs: float = 60.0

    def get_delay(self, attempt: int) -> float:
        delay = self.initial_delay_secs * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay_secs)
