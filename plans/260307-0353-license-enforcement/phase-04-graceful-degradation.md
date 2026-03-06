---
title: "Phase 4: Graceful Degradation (Circuit Breaker)"
description: "Implement circuit breaker pattern for remote API failures"
status: pending
priority: P2
effort: 1.5h
---

# Phase 4: Graceful Degradation Implementation

## Objective

Implement circuit breaker pattern để tự động switch sang offline mode sau 3 failures và auto-retry sau 24h.

## Circuit Breaker States

```
┌─────────────┐
│   CLOSED    │ ← Normal operation, remote API working
│  (healthy)  │
└──────┬──────┘
       │ Failure detected
       ▼
┌─────────────┐
│    OPEN     │ ← Remote API failing, block requests
│  (failing)  │   Switch to offline mode immediately
└──────┬──────┘
       │ Timeout expires (24h)
       ▼
┌─────────────┐
│  HALF-OPEN  │ ← Test if API recovered
│  (testing)  │   Allow 1 request to probe
└──────┬──────┘
       │ Success → CLOSED
       │ Failure → OPEN
```

## State Machine

| State | Behavior | Duration |
|-------|----------|----------|
| CLOSED | Normal remote validation | Until 3 consecutive failures |
| OPEN | Skip remote, use offline grace | 24 hours |
| HALF-OPEN | Probe remote API | 1 request, then back to CLOSED or OPEN |

## New File: src/raas/circuit_breaker.py

```python
"""
Circuit Breaker — ROIaaS Phase 6g

Automatic failover for remote license API.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum
import json
from pathlib import Path


class CircuitState(Enum):
    CLOSED = "closed"      # Normal
    OPEN = "open"          # Failing
    HALF_OPEN = "half_open"  # Testing


class CircuitBreaker:
    """Circuit breaker for remote license API."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 86400,  # 24 hours
        state_file: Optional[Path] = None,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._state_file = state_file or Path.home() / ".mekong" / "raas" / "circuit_breaker.json"
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = CircuitState.CLOSED
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file."""
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
                self._failure_count = data.get("failure_count", 0)
                if data.get("last_failure_time"):
                    self._last_failure_time = datetime.fromisoformat(data["last_failure_time"])
                self._state = CircuitState(data.get("state", "closed"))

                # Check if recovery timeout expired
                if self._state == CircuitState.OPEN and self._last_failure_time:
                    elapsed = (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
                    if elapsed >= self._recovery_timeout:
                        self._state = CircuitState.HALF_OPEN
            except Exception:
                pass  # Start fresh on error

    def _save_state(self) -> None:
        """Persist state to file."""
        data = {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
        }
        self._state_file.write_text(json.dumps(data, indent=2))

    def record_success(self) -> None:
        """Record successful remote validation."""
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
        self._save_state()

    def record_failure(self) -> None:
        """Record failed remote validation."""
        self._failure_count += 1
        self._last_failure_time = datetime.now(timezone.utc)

        if self._state == CircuitState.HALF_OPEN:
            # Failed probe, back to OPEN
            self._state = CircuitState.OPEN
        elif self._failure_count >= self._failure_threshold:
            # Threshold reached, open circuit
            self._state = CircuitState.OPEN

        self._save_state()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        # Check for timeout transition
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
            if elapsed >= self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._save_state()
        return self._state

    @property
    def should_allow_remote(self) -> bool:
        """Check if remote validation should be attempted."""
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.HALF_OPEN:
            return True  # Allow probe
        return False  # OPEN - skip remote

    @property
    def should_use_offline_grace(self) -> bool:
        """Check if offline grace period should be used."""
        return self._state in (CircuitState.OPEN, CircuitState.HALF_OPEN)

    def get_status(self) -> dict:
        """Get circuit breaker status for debugging."""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "threshold": self._failure_threshold,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "recovery_timeout": self._recovery_timeout,
        }

    def reset(self) -> None:
        """Manual reset (for debugging)."""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
        self._save_state()


# Singleton
_breaker: Optional[CircuitBreaker] = None


def get_circuit_breaker() -> CircuitBreaker:
    """Get global circuit breaker instance."""
    global _breaker
    if _breaker is None:
        _breaker = CircuitBreaker()
    return _breaker


def should_use_remote_validation() -> bool:
    """Check if remote validation should be attempted."""
    return get_circuit_breaker().should_allow_remote


def record_remote_success() -> None:
    """Record successful remote validation."""
    get_circuit_breaker().record_success()


def record_remote_failure() -> None:
    """Record failed remote validation."""
    get_circuit_breaker().record_failure()


__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "get_circuit_breaker",
    "should_use_remote_validation",
    "record_remote_success",
    "record_remote_failure",
]
```

## Integration with RaasLicenseGate

**File:** `src/lib/raas_gate.py`

```python
from src.raas.circuit_breaker import (
    get_circuit_breaker,
    record_remote_success,
    record_remote_failure,
    CircuitState,
)

def validate_remote(self, license_key: str) -> Tuple[bool, Optional[dict], str]:
    breaker = get_circuit_breaker()

    # Skip remote if circuit is OPEN
    if not breaker.should_allow_remote:
        # Use offline grace period
        return self._validate_offline_grace(license_key)

    try:
        response = requests.post(
            f"{self._remote_url}/api/v1/license/validate",
            json={"license_key": license_key},
            timeout=5,
        )

        if response.status_code == 200:
            record_remote_success()  # Circuit breaker
            # ... process success ...

        elif response.status_code in (401, 403):
            record_remote_success()  # Auth errors don't trip breaker
            # ... handle auth error ...

        else:
            record_remote_failure()  # Trip the breaker
            return self._validate_offline_grace(license_key)

    except requests.exceptions.RequestException as e:
        record_remote_failure()  # Trip the breaker
        return self._validate_offline_grace(license_key)
```

## Implementation Steps

1. [ ] Create `src/raas/circuit_breaker.py`
2. [ ] Implement state machine logic
3. [ ] Add persistence (JSON file)
4. [ ] Integrate with `RaasLicenseGate.validate_remote()`
5. [ ] Add debug command: `mekong license circuit-status`

## Output Files

- New: `src/raas/circuit_breaker.py`
- Modified: `src/lib/raas_gate.py`
- New command: `src/commands/license_circuit_status.py`

## Success Criteria

- [ ] Tự động switch sang offline sau 3 failures
- [ ] Auto-retry sau 24h
- [ ] State persisted across CLI invocations
- [ ] Debug command để check status
- [ ] Không false positives (auth errors không trip breaker)
