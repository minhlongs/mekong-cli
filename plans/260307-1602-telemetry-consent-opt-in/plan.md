---
title: "Post-GA Telemetry Consent & Opt-In Analytics"
description: "Privacy-compliant telemetry consent prompt và opt-in analytics collection cho mekong-cli"
status: in_progress
priority: P0
effort: 3h
branch: master
tags: [telemetry, analytics, privacy, gdpr, consent]
created: 2026-03-07
---

# Post-GA Telemetry Consent & Opt-In Analytics

## Context Links
- **Analytics Dashboard**: `/Users/macbookprom1/mekong-cli/src/analytics/dashboard_service.py`
- **Telemetry Module**: `/Users/macbookprom1/mekong-cli/src/telemetry/`
- **Privacy Compliance**: GDPR, CCPA requirements

## Overview

**Goal**: Implement telemetry consent prompt và opt-in analytics collection:
- Ask user permission on first run
- Anonymized usage data collection (command frequency, error rates, session duration)
- Transmit to existing Analytics dashboard backend when consent granted
- Full privacy compliance (GDPR, CCPA)

**Scope**:
- Consent prompt on CLI first run
- Store consent preference locally
- Track anonymized usage events
- Batch upload to analytics backend
- Easy opt-out mechanism

## Architecture

### Consent Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CLI Startup                                                   │
│    ↓                                                             │
│ 2. Check Consent Store (~/.mekong/telemetry-consent.json)       │
│    ↓                                                             │
│ 3. No consent? → Show Prompt                                    │
│    ↓                                                             │
│ 4. User Chooses: Opt-In or Opt-Out                              │
│    ↓                                                             │
│ 5. Store Preference + Generate Anonymous ID                     │
│    ↓                                                             │
│ 6. If Opt-In: Track Usage Events                                │
│    ↓                                                             │
│ 7. Batch Upload (every N commands or session end)               │
└─────────────────────────────────────────────────────────────────┘
```

### Data Collected (Anonymized)

| Event Type | Data Points | PII |
|------------|-------------|-----|
| `command_executed` | command_name, duration_ms, exit_code, error_type | ❌ |
| `session_started` | session_id, cli_version, python_version, os | ❌ |
| `session_ended` | session_id, duration_ms, commands_count | ❌ |
| `error_occurred` | error_type, stack_trace_hash, command_name | ❌ |

**NOT Collected:**
- ❌ License keys
- ❌ File paths
- ❌ API keys/secrets
- ❌ Email addresses
- ❌ IP addresses (anonymized to country level only if enabled)

### Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│ mekong-cli                                                       │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ src/core/telemetry_consent.py                               │ │
│ │  - ConsentManager: Check/store consent preference           │ │
│ │  - ConsentPrompt: Rich-based interactive prompt             │ │
│ │  - Generate anonymous session ID                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ src/core/telemetry_collector.py                             │ │
│ │  - TelemetryCollector: Track usage events                   │ │
│ │  - Event batching & buffering                               │ │
│ │  - Anonymization layer                                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ src/core/telemetry_uploader.py                              │ │
│ │  - Batch upload to analytics backend                        │ │
│ │  - Retry logic with exponential backoff                     │ │
│ │  - Offline queue (upload when online)                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ Analytics Backend (existing)                                     │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ src/db/tables/telemetry_events.sql                          │ │
│ │  - Store telemetry events                                   │ │
│ │  - Aggregate for dashboard                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Files to Create

| File | Purpose | Effort |
|------|---------|--------|
| `src/core/telemetry_consent.py` | Consent management & prompt | 1h |
| `src/core/telemetry_collector.py` | Usage event collection | 1h |
| `src/core/telemetry_uploader.py` | Batch upload to backend | 30m |
| `src/db/tables/telemetry_events.sql` | Database schema | 15m |
| `src/db/queries/telemetry_queries.py` | Database queries | 15m |

## Files to Modify

| File | Changes | Effort |
|------|---------|--------|
| `src/main.py` | Hook consent check at startup | 15m |
| `src/core/orchestrator.py` | Track command execution events | 15m |
| `src/core/exceptions.py` | Add telemetry exceptions | 10m |

## Implementation Steps

### Step 1: Consent Manager (`telemetry_consent.py`)

```python
"""
Telemetry Consent Manager — Post-GA Privacy Compliance

Handles:
- Consent prompt on first run
- Store/retrieve consent preference
- Generate anonymous session IDs
- Opt-in/opt-out management
"""

import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel

console = Console()

@dataclass
class ConsentPreferences:
    """User telemetry consent preferences."""
    consent_given: bool = False
    consent_timestamp: str = ""
    anonymous_id: str = ""
    version: str = "1.0"  # Consent schema version


class ConsentManager:
    """
    Manage telemetry consent preferences.

    Storage: ~/.mekong/telemetry-consent.json
    """

    def __init__(self, config_dir: str = "~/.mekong"):
        self._config_dir = Path(config_dir).expanduser()
        self._consent_file = self._config_dir / "telemetry-consent.json"
        self._preferences: ConsentPreferences | None = None

    def ensure_config_dir(self) -> None:
        """Create config directory if not exists."""
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def load_consent(self) -> ConsentPreferences | None:
        """Load consent preferences from file."""
        if self._preferences:
            return self._preferences

        if not self._consent_file.exists():
            return None

        try:
            with open(self._consent_file, "r") as f:
                data = json.load(f)
                self._preferences = ConsentPreferences(**data)
                return self._preferences
        except (json.JSONDecodeError, KeyError):
            return None

    def save_consent(self, preferences: ConsentPreferences) -> None:
        """Save consent preferences to file."""
        self.ensure_config_dir()
        with open(self._consent_file, "w") as f:
            json.dump(asdict(preferences), f, indent=2)
        self._preferences = preferences

    def has_consent(self) -> bool:
        """Check if user has given consent."""
        preferences = self.load_consent()
        return preferences is not None and preferences.consent_given

    def prompt_consent(self) -> ConsentPreferences:
        """Show interactive consent prompt."""
        console.print(Panel(
            """[bold cyan]📊 Help Improve Mekong CLI[/bold cyan]

Would you like to send [green]anonymous usage data[/green] to help improve Mekong CLI?

[dim]We collect:[/dim]
• Command names (e.g., "cook", "plan", "roi status")
• Session duration and command count
• Error rates (anonymized error types only)
• CLI version and OS information

[dim]We DO NOT collect:[/dim]
• License keys or API secrets
• File paths or code content
• IP addresses or personal information
• Any identifiable data

[yellow]You can change this setting anytime:[/yellow]
  mekong telemetry enable   # Opt-in
  mekong telemetry disable  # Opt-out
  mekong telemetry status   # Check status
""",
            title="🔒 Privacy-First Telemetry",
            border_style="cyan",
        ))

        consent = Confirm.ask(
            "\n[bold]Would you like to enable anonymous telemetry?[/bold]",
            default=True,
        )

        preferences = ConsentPreferences(
            consent_given=consent,
            consent_timestamp=datetime.now(timezone.utc).isoformat(),
            anonymous_id=str(uuid.uuid4()),
            version="1.0",
        )

        if consent:
            console.print("\n[green]✓ Telemetry enabled. Thank you![/green]\n")
        else:
            console.print("\n[yellow]✓ Telemetry disabled. No data will be collected.[/yellow]\n")

        self.save_consent(preferences)
        return preferences

    def get_anonymous_id(self) -> str | None:
        """Get anonymous user ID (only if consent given)."""
        preferences = self.load_consent()
        if preferences and preferences.consent_given:
            return preferences.anonymous_id
        return None

    def enable(self) -> ConsentPreferences:
        """Enable telemetry."""
        preferences = self.load_consent() or ConsentPreferences()
        preferences.consent_given = True
        preferences.consent_timestamp = datetime.now(timezone.utc).isoformat()
        if not preferences.anonymous_id:
            preferences.anonymous_id = str(uuid.uuid4())
        self.save_consent(preferences)
        return preferences

    def disable(self) -> ConsentPreferences:
        """Disable telemetry."""
        preferences = self.load_consent() or ConsentPreferences()
        preferences.consent_given = False
        self.save_consent(preferences)
        return preferences

    def get_status(self) -> dict:
        """Get consent status."""
        preferences = self.load_consent()
        if not preferences:
            return {
                "status": "not_set",
                "message": "Consent not set. Run 'mekong telemetry enable' to opt-in.",
            }
        return {
            "status": "enabled" if preferences.consent_given else "disabled",
            "anonymous_id": preferences.anonymous_id if preferences.consent_given else None,
            "consent_timestamp": preferences.consent_timestamp,
            "version": preferences.version,
        }
```

### Step 2: Telemetry Collector (`telemetry_collector.py`)

```python
"""
Telemetry Collector — Usage Event Collection

Collects anonymized usage events:
- command_executed
- session_started
- session_ended
- error_occurred
"""

import json
import os
import time
import atexit
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib

from .telemetry_consent import ConsentManager


@dataclass
class TelemetryEvent:
    """Telemetry event."""
    event_type: str
    anonymous_id: str
    timestamp: str
    session_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    cli_version: str = "3.0.0"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class TelemetryCollector:
    """
    Collect anonymized usage telemetry.

    Events are buffered and uploaded in batches.
    """

    def __init__(self, consent_manager: Optional[ConsentManager] = None):
        self._consent_manager = consent_manager or ConsentManager()
        self._buffer: List[TelemetryEvent] = []
        self._session_id: Optional[str] = None
        self._session_start: Optional[float] = None
        self._commands_count = 0
        self._max_buffer_size = 50  # Upload after N events
        self._storage_file = Path.home() / ".mekong" / "telemetry-buffer.json"

        # Register cleanup on exit
        atexit.register(self._flush_on_exit)

    def _ensure_anonymous_id(self) -> Optional[str]:
        """Get anonymous ID (only if consent given)."""
        if not self._consent_manager.has_consent():
            return None
        return self._consent_manager.get_anonymous_id()

    def _get_session_id(self) -> str:
        """Get or create session ID."""
        if not self._session_id:
            import uuid
            self._session_id = str(uuid.uuid4())
            self.session_start()
        return self._session_id

    def _hash_error(self, error_message: str) -> str:
        """Hash error message for anonymization."""
        return hashlib.sha256(error_message.encode()).hexdigest()[:16]

    def session_start(self) -> None:
        """Record session start event."""
        anonymous_id = self._ensure_anonymous_id()
        if not anonymous_id:
            return

        self._session_start = time.time()

        event = TelemetryEvent(
            event_type="session_started",
            anonymous_id=anonymous_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self._get_session_id(),
            properties={
                "cli_version": "3.0.0",
                "python_version": os.popen("python3 --version").read().strip(),
                "os": os.uname().sysname,
            },
        )
        self._buffer.append(event)
        self._check_buffer()

    def command_executed(
        self,
        command_name: str,
        duration_ms: int,
        exit_code: int,
        error_type: Optional[str] = None,
    ) -> None:
        """Record command execution event."""
        anonymous_id = self._ensure_anonymous_id()
        if not anonymous_id:
            return

        self._commands_count += 1

        properties = {
            "command": command_name,
            "duration_ms": duration_ms,
            "exit_code": exit_code,
            "success": exit_code == 0,
        }

        if error_type:
            properties["error_type_hash"] = self._hash_error(error_type)

        event = TelemetryEvent(
            event_type="command_executed",
            anonymous_id=anonymous_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self._get_session_id(),
            properties=properties,
        )
        self._buffer.append(event)
        self._check_buffer()

    def error_occurred(
        self,
        error_type: str,
        error_message: str,
        command_name: Optional[str] = None,
    ) -> None:
        """Record error event."""
        anonymous_id = self._ensure_anonymous_id()
        if not anonymous_id:
            return

        event = TelemetryEvent(
            event_type="error_occurred",
            anonymous_id=anonymous_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self._get_session_id(),
            properties={
                "error_type": error_type,
                "error_message_hash": self._hash_error(error_message),
                "command": command_name,
            },
        )
        self._buffer.append(event)
        self._check_buffer()

    def session_end(self) -> None:
        """Record session end event."""
        anonymous_id = self._ensure_anonymous_id()
        if not anonymous_id:
            return

        duration_ms = 0
        if self._session_start:
            duration_ms = int((time.time() - self._session_start) * 1000)

        event = TelemetryEvent(
            event_type="session_ended",
            anonymous_id=anonymous_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self._get_session_id(),
            properties={
                "duration_ms": duration_ms,
                "commands_count": self._commands_count,
            },
        )
        self._buffer.append(event)
        self._flush()

    def _check_buffer(self) -> None:
        """Check if buffer needs upload."""
        if len(self._buffer) >= self._max_buffer_size:
            self._flush()

    def _flush(self) -> None:
        """Flush buffer to storage."""
        if not self._buffer:
            return

        # Save to local buffer file
        self._storage_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing buffer
        existing = []
        if self._storage_file.exists():
            try:
                with open(self._storage_file, "r") as f:
                    existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

        # Append new events
        existing.extend([e.to_dict() for e in self._buffer])

        # Save
        with open(self._storage_file, "w") as f:
            json.dump(existing, f, indent=2)

        self._buffer = []

    def _flush_on_exit(self) -> None:
        """Flush on program exit."""
        self.session_end()
        self._flush()

    def get_pending_events(self) -> List[dict]:
        """Get pending events from storage."""
        if not self._storage_file.exists():
            return []

        try:
            with open(self._storage_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def clear_buffer(self) -> None:
        """Clear local buffer."""
        if self._storage_file.exists():
            self._storage_file.unlink()
```

### Step 3: Telemetry Uploader (`telemetry_uploader.py`)

```python
"""
Telemetry Uploader — Batch Upload to Analytics Backend

Uploads telemetry events to existing analytics backend.
"""

import asyncio
import json
import logging
import os
from typing import List, Optional
from pathlib import Path
import requests

from .telemetry_consent import ConsentManager
from .telemetry_collector import TelemetryCollector

logger = logging.getLogger(__name__)


class TelemetryUploader:
    """
    Upload telemetry events to analytics backend.

    Backend endpoint: POST /api/v1/telemetry/events
    """

    def __init__(
        self,
        collector: TelemetryCollector,
        consent_manager: ConsentManager,
        backend_url: Optional[str] = None,
    ):
        self._collector = collector
        self._consent_manager = consent_manager
        self._backend_url = backend_url or os.getenv(
            "TELEMETRY_BACKEND_URL",
            "https://api.mekong.dev/api/v1/telemetry/events",
        )
        self._batch_size = 100

    def upload_batch(self) -> int:
        """Upload pending events to backend."""
        if not self._consent_manager.has_consent():
            return 0

        events = self._collector.get_pending_events()
        if not events:
            return 0

        # Upload in batches
        uploaded = 0
        for i in range(0, len(events), self._batch_size):
            batch = events[i : i + self._batch_size]
            if self._upload_events(batch):
                uploaded += len(batch)

        # Clear uploaded events
        if uploaded > 0:
            self._collector.clear_buffer()

        return uploaded

    def _upload_events(self, events: List[dict]) -> bool:
        """Upload events to backend."""
        try:
            response = requests.post(
                self._backend_url,
                json={"events": events},
                headers={
                    "Content-Type": "application/json",
                    "X-Anonymous-ID": self._consent_manager.get_anonymous_id(),
                },
                timeout=10,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.warning(f"Telemetry upload failed: {e}")
            return False

    async def upload_async(self) -> int:
        """Async upload."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.upload_batch)
```

### Step 4: Database Schema (`telemetry_events.sql`)

```sql
-- Telemetry Events Table
CREATE TABLE IF NOT EXISTS telemetry_events (
    id SERIAL PRIMARY KEY,
    anonymous_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    cli_version VARCHAR(20),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX idx_telemetry_anonymous_id ON telemetry_events(anonymous_id);
CREATE INDEX idx_telemetry_event_type ON telemetry_events(event_type);
CREATE INDEX idx_telemetry_timestamp ON telemetry_events(timestamp DESC);
CREATE INDEX idx_telemetry_session_id ON telemetry_events(session_id);

-- Aggregated daily stats view
CREATE VIEW telemetry_daily_stats AS
SELECT
    DATE(timestamp) AS date,
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT anonymous_id) AS unique_users,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM telemetry_events
GROUP BY DATE(timestamp), event_type;
```

### Step 5: CLI Commands (`telemetry_commands.py`)

```python
"""
Telemetry CLI Commands

Commands:
- mekong telemetry status
- mekong telemetry enable
- mekong telemetry disable
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.telemetry_consent import ConsentManager

console = Console()
app = typer.Typer(name="telemetry", help="📊 Telemetry consent management")


@app.command("status")
def telemetry_status():
    """Show telemetry consent status."""
    manager = ConsentManager()
    status = manager.get_status()

    table = Table(title="📊 Telemetry Status")
    table.add_column("Property", style="dim")
    table.add_column("Value")

    for key, value in status.items():
        if value:
            table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)


@app.command("enable")
def telemetry_enable():
    """Enable telemetry."""
    manager = ConsentManager()
    preferences = manager.enable()
    console.print(f"[green]✓ Telemetry enabled[/green]")
    console.print(f"Anonymous ID: {preferences.anonymous_id}")


@app.command("disable")
def telemetry_disable():
    """Disable telemetry."""
    manager = ConsentManager()
    manager.disable()
    console.print("[yellow]✓ Telemetry disabled[/yellow]")
    console.print("No data will be collected.")
```

## Success Criteria

- [ ] Consent prompt shown on first run
- [ ] User can opt-in/opt-out
- [ ] Preference stored persistently
- [ ] Events tracked only with consent
- [ ] Data anonymized (no PII)
- [ ] Batch upload working
- [ ] CLI commands: `telemetry status/enable/disable`
- [ ] Integration with existing analytics dashboard

## Privacy Compliance

| Requirement | Implementation |
|-------------|----------------|
| Explicit consent | Interactive prompt with clear explanation |
| Easy opt-out | `mekong telemetry disable` command |
| Data minimization | Only essential usage metrics |
| Anonymization | No PII, hashed error messages |
| Transparency | Clear documentation of data collected |
| User control | Status, enable, disable commands |

## Next Steps

1. Create `telemetry_consent.py` with ConsentManager
2. Create `telemetry_collector.py` with event tracking
3. Create `telemetry_uploader.py` with batch upload
4. Create database migration for telemetry_events table
5. Create CLI commands for consent management
6. Integrate with main.py startup
7. Test end-to-end flow

---

## Unresolved Questions

1. **Backend Endpoint URL**: What is the production telemetry ingestion URL?
2. **Data Retention**: How long to keep telemetry data? (recommend: 90 days)
3. **Rate Limiting**: Should we limit upload frequency per user?