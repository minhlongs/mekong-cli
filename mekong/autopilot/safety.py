# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Safety budget — caps the autopilot before it can do too much damage.

Tracks iterations, tokens consumed, MCU credits, consecutive failures, and
provides a kill switch (Ctrl-C → persisted abort flag).
"""

from __future__ import annotations

import json
import signal
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class SafetyBudget:
    max_iter: int = 12
    max_tokens: int = 800_000  # 1M context with 200k headroom
    max_mcu: int = 50
    max_consec_failures: int = 3
    timeout_secs: int = 60 * 60  # 1 hour hard cap
    state_file: Path | None = None

    iter_count: int = 0
    tokens_used: int = 0
    mcu_used: int = 0
    consec_failures: int = 0
    aborted: bool = False
    started_at: float = field(default_factory=time.time)

    def install_signal_handlers(self) -> None:
        """Trap SIGINT/SIGTERM → set aborted=True instead of nuking mid-write."""
        def handler(signum, _frame):  # type: ignore[no-untyped-def]
            self.aborted = True
            self._persist()
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    def exhausted(self) -> tuple[bool, str]:
        if self.aborted:
            return True, "aborted by user"
        if self.iter_count >= self.max_iter:
            return True, f"max_iter={self.max_iter} reached"
        if self.tokens_used >= self.max_tokens:
            return True, f"max_tokens={self.max_tokens} reached"
        if self.mcu_used >= self.max_mcu:
            return True, f"max_mcu={self.max_mcu} reached"
        if self.consec_failures >= self.max_consec_failures:
            return True, f"too many consecutive failures ({self.consec_failures})"
        if (time.time() - self.started_at) > self.timeout_secs:
            return True, f"timeout {self.timeout_secs}s reached"
        return False, ""

    def record_iter(self) -> None:
        self.iter_count += 1
        self._persist()

    def record_tokens(self, n: int) -> None:
        self.tokens_used += n
        self._persist()

    def record_mcu(self, n: int = 1) -> None:
        self.mcu_used += n
        self._persist()

    def record_success(self) -> None:
        self.consec_failures = 0
        self._persist()

    def record_failure(self) -> None:
        self.consec_failures += 1
        self._persist()

    def _persist(self) -> None:
        if self.state_file is None:
            return
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        d = asdict(self)
        d["state_file"] = str(self.state_file)
        self.state_file.write_text(json.dumps(d, indent=2), encoding="utf-8")
