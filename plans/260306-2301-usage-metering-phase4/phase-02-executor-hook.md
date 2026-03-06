---
title: "Phase 2 — Executor Integration Hook"
description: "Add _record_usage() hook to RecipeExecutor._execute_shell_step()"
status: completed
priority: P2
effort: 1h
parent_plan: 260306-2301-usage-metering-phase4
depends_on: phase-01, phase-06
---

# Phase 2 — Executor Integration Hook

## Context Links

- Parent Plan: `plans/260306-2301-usage-metering-phase4/plan.md`
- Depends: Phase 1 (UsageQueue), Phase 6 (License Parsing)
- Target: `src/core/executor.py`

## Overview

Hook usage recording into `RecipeExecutor._execute_shell_step()` to capture every successful command execution.

## Implementation

### Step 1: Add Imports

```python
# src/core/executor.py
import os
import hashlib
from datetime import datetime

from src.lib.usage_queue import get_queue, UsageQueue
from src.lib.license_generator import parse_license_key
from src.config.logging_config import get_logger
```

### Step 2: Initialize in __init__

```python
class RecipeExecutor:
    """Executes a Recipe step by step, returning structured results."""

    def __init__(self, recipe: Recipe) -> None:
        self.recipe = recipe
        self.console = Console()
        self._logger = get_logger(__name__)
        self._usage_queue = get_queue()
```

### Step 3: Add _record_usage Method

```python
    async def _record_usage(
        self,
        command: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Record usage for a successful command execution.

        Args:
            command: The shell command that was executed
            metadata: Execution metadata (exit_code, duration, etc.)
        """
        try:
            # Extract license key from env var
            license_key = os.getenv("RAAS_LICENSE_KEY")
            if not license_key:
                self._logger.debug("usage.no_license_key", reason="Env var not set")
                return

            # Parse key to extract key_id and tier
            is_valid, parsed, error = parse_license_key(license_key)
            if not is_valid:
                self._logger.warning(
                    "usage.invalid_license",
                    reason=error,
                )
                return

            key_id = parsed["key_id"]
            tier = parsed["tier"]

            # Generate idempotency key
            timestamp = datetime.utcnow()
            date_str = timestamp.strftime("%Y-%m-%d")
            command_hash = hashlib.sha256(command.encode()).hexdigest()[:16]
            idempotency_key = f"{key_id}:{command_hash}:{date_str}"

            # Enqueue usage event
            await self._usage_queue.enqueue(
                key_id=key_id,
                tier=tier,
                command=command,
                metadata={
                    **metadata,
                    "idempotency_key": idempotency_key,
                    "timestamp": timestamp.isoformat(),
                },
            )

            self._logger.info(
                "usage.captured",
                key_id=key_id,
                tier=tier,
                command=command[:100],  # Truncate for logs
            )

        except Exception as e:
            # Log error but don't fail the command
            self._logger.error(
                "usage.record_failed",
                error=str(e),
                command=command[:100],
            )
```

### Step 4: Hook into _execute_shell_step

```python
    def _execute_shell_step(self, step: RecipeStep) -> ExecutionResult:
        """Execute shell command step with automatic retry on failure."""
        command = step.description.strip()
        # ... existing retry logic ...

        for attempt in range(1, max_attempts + 1):
            # ... existing execution code ...

            try:
                process = subprocess.run(
                    command, shell=True, check=True, text=True, capture_output=True,
                )

                # ... existing output display ...

                result = ExecutionResult(
                    exit_code=process.returncode,
                    stdout=process.stdout or "",
                    stderr=process.stderr or "",
                    metadata={
                        "mode": "shell",
                        "command": command,
                        "attempt": attempt,
                    },
                )

                # === HOOK: Record usage on success ===
                if process.returncode == 0:
                    # Fire-and-forget async call
                    asyncio.create_task(
                        self._record_usage(command, result.metadata)
                    )
                # ====================================

                return result

            except subprocess.CalledProcessError as e:
                # ... existing error handling ...
```

### Step 5: Add asyncio Import

```python
import asyncio
import subprocess
import time
# ... rest of imports
```

## Success Criteria

- [ ] Every successful command triggers `_record_usage()`
- [ ] License key parsed correctly from env var
- [ ] Invalid keys logged but don't fail command
- [ ] Idempotency key generated per command
- [ ] Errors logged but don't interrupt execution
- [ ] All events logged with structlog

## Todo List

- [ ] Add imports to executor.py
- [ ] Initialize UsageQueue and logger in __init__
- [ ] Implement _record_usage() method
- [ ] Hook into _execute_shell_step after successful execution
- [ ] Test with sample commands

## Risks

- **Async in sync method**: Using `asyncio.create_task()` fire-and-forget
- **License key not set**: Graceful fallback, just log debug
- **Performance**: Minimal overhead (just queue enqueue)

## Unresolved Questions

1. Should we wait for queue flush or fire-and-forget? (Proposed: fire-and-forget for perf)
