# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Configurable command-based verification gates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.mekongcli.core.execution import LocalExecutor


@dataclass(frozen=True)
class VerificationGate:
    name: str
    command: str
    required: bool = True
    timeout_seconds: int = 120


class VerificationPipeline:
    """Runs verification gates and returns persisted result payloads."""

    VALID_PROFILES = frozenset({"standard", "smoke", "none"})
    STANDARD_GATES = (
        VerificationGate("pytest", "pytest", timeout_seconds=300),
        VerificationGate("ruff", "ruff check .", timeout_seconds=180),
        VerificationGate("mypy", "mypy .", timeout_seconds=300),
        VerificationGate("bandit", "bandit -r .", timeout_seconds=300),
        VerificationGate("coverage", "coverage run -m pytest", timeout_seconds=420),
    )
    SMOKE_GATES = (
        VerificationGate("python-import", "python3 -c 'import src.main'", timeout_seconds=30),
    )

    def __init__(self, cwd: str | Path = ".", gates: Iterable[VerificationGate] | None = None) -> None:
        self.cwd = Path(cwd)
        self.gates = list(gates) if gates is not None else list(self.STANDARD_GATES)

    @classmethod
    def profile_options(cls) -> str:
        return ", ".join(sorted(cls.VALID_PROFILES))

    @classmethod
    def validate_profile(cls, profile: str) -> None:
        if profile not in cls.VALID_PROFILES:
            raise ValueError(
                f"Unknown verification profile '{profile}'. Expected one of: {cls.profile_options()}"
            )

    @classmethod
    def for_profile(cls, profile: str, cwd: str | Path = ".") -> "VerificationPipeline":
        cls.validate_profile(profile)
        if profile == "smoke":
            return cls(cwd=cwd, gates=cls.SMOKE_GATES)
        if profile == "none":
            return cls(cwd=cwd, gates=())
        return cls(cwd=cwd)

    def run(self) -> tuple[bool, list[dict[str, object]]]:
        results: list[dict[str, object]] = []
        passed = True
        for gate in self.gates:
            outcome = LocalExecutor(self.cwd, timeout_seconds=gate.timeout_seconds).run(gate.command)
            gate_passed = outcome.success
            if gate.required and not gate_passed:
                passed = False
            results.append(
                {
                    "name": gate.name,
                    "command": gate.command,
                    "required": gate.required,
                    "passed": gate_passed,
                    "exit_code": outcome.exit_code,
                    "stdout": outcome.stdout,
                    "stderr": outcome.stderr,
                    "duration_ms": outcome.duration_ms,
                    "blocked_reason": outcome.blocked_reason,
                }
            )
        return passed, results
