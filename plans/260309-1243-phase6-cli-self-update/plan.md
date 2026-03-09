---
title: "Phase 6: CLI Self-Update Mechanism - Implementation Plan"
description: "Complete CLI self-update system with RaaS Gateway validation, critical enforcement, and usage metering"
status: in-progress
priority: P1
effort: 6h
branch: master
tags: [phase-6, cli, auto-update, raas-gateway]
created: 2026-03-09
---

# Phase 6: CLI Self-Update Mechanism

## Executive Summary

Secure CLI self-update mechanism that checks RaaS Gateway for latest version, enforces critical updates, validates signatures, and logs usage for billing.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  mekong CLI Startup (src/main.py)                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Check MEKONG_NO_UPDATE_CHECK env → skip if set                     │
│  2. Spawn background update check (non-blocking async)                 │
│  3. Call RaaS Gateway: GET /v1/cli/version                             │
│  4. Compare versions → if newer available:                             │
│     - Check if critical/security update → enforce                     │
│     - Notify user: "mekong update install"                              │
│  5. Log usage event → Phase 4 tracker                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  RaaS Gateway (apps/raas-gateway/index.js)                              │
├─────────────────────────────────────────────────────────────────────────┤
│  GET /v1/cli/version                                                    │
│  - Auth: JWT/mk_ API key (existing authenticate())                     │
│  - Rate limit: Per tenant (checkRateLimit())                           │
│  - Usage track: Version check event (trackUsage())                     │
│  - Response: {latest_version, is_critical, download_url, ...}          │
│  - Critical flags from KV: cli_critical_versions                       │
│  - Security flags from KV: cli_security_versions                       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Existing Components (Already Implemented)

| Component | File | Status |
|-----------|------|--------|
| Gateway Handler | `apps/raas-gateway/src/cli-version-handler.js` | DONE |
| Gateway Route | `apps/raas-gateway/index.js` (line 359-362) | DONE |
| Update Checker | `src/cli/update_checker.py` | DONE |
| Auto Updater | `src/cli/auto_updater.py` | DONE |
| Update Commands | `src/cli/update_commands.py` | DONE |
| Startup Integration | `src/main.py` (line 480-487) | DONE |

## Gap Analysis

What's missing to complete Phase 6:

1. **RaaS Gateway Integration in Update Checker** - Currently uses GitHub Releases API directly
2. **Critical Update Enforcement** - Block CLI execution on critical updates
3. **Install/Rollback Commands** - Wire up `mekong update install` and `mekong update rollback`
4. **Status Command** - Add `mekong update status` for current state
5. **Tests** - Unit tests for all components

## Implementation Phases

### Phase 1: RaaS Gateway Integration (1h)

**Goal:** Update checker uses RaaS Gateway instead of GitHub Releases

**Files to Modify:**
- `src/cli/update_checker.py` - Change `check_version()` to call `/v1/cli/version`
- `src/cli/auto_updater.py` - Add RaaS Gateway fallback

**Implementation:**
```python
# In update_checker.py - check_version() method
async def check_version(self) -> Optional[UpdateAvailable]:
    """Check RaaS Gateway for latest version."""
    try:
        current_version = importlib.metadata.version("mekong-cli")
    except importlib.metadata.PackageNotFoundError:
        current_version = "0.0.0"

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                self.gateway.get, "/v1/cli/version"
            ),
            timeout=CHECK_TIMEOUT_SECONDS
        )

        data = response.data
        latest_version = data.get("latest_version", current_version)

        # Update cache
        self.cache = UpdateCache(
            checked_at=datetime.now(timezone.utc),
            latest_version=latest_version,
            update_info=data,
        )
        self._save_cache(self.cache)

        if self._is_newer_version(latest_version, current_version):
            return UpdateAvailable(
                current_version=current_version,
                latest_version=latest_version,
                download_url=data.get("download_url", ""),
                checksum_url=data.get("checksum_url", ""),
                signature_url=data.get("signature_url", ""),
                is_critical=data.get("is_critical", False),
                is_security_update=data.get("is_security_update", False),
                release_notes=data.get("release_notes", ""),
                released_at=data.get("released_at", ""),
                changelog_url=data.get("changelog_url", ""),
            )

        return None
    except asyncio.TimeoutError:
        return None
    except Exception:
        return None
```

**Success Criteria:**
- [ ] `update_checker.py` calls RaaS Gateway `/v1/cli/version`
- [ ] Gateway returns version info with `is_critical` and `is_security_update` flags
- [ ] Fallback to GitHub Releases if gateway unreachable

---

### Phase 2: Critical Update Enforcement (1h)

**Goal:** Block CLI execution when critical update available

**Files to Modify:**
- `src/cli/update_checker.py` - Add `check_critical_update()` method
- `src/main.py` - Add critical check in `_validate_startup_license()`
- `src/cli/update_notification.py` - Add critical update notification

**Implementation:**
```python
# In update_checker.py
def check_critical_update(self) -> Optional[UpdateAvailable]:
    """Check for critical update and return if blocking required."""
    update = self.check_version_sync()  # Sync version check

    if update and update.is_critical:
        # Store critical update info for enforcement
        self._mark_critical_update_pending(update)
        return update

    return None

def should_block_execution(self) -> bool:
    """Check if CLI execution should be blocked."""
    if not self.cache.update_info:
        return False

    # Check if current version is in critical list
    critical_versions = self.cache.update_info.get("critical_versions", [])
    current_version = self.get_current_version()

    return current_version in critical_versions
```

```python
# In main.py - _validate_startup_license()
def _validate_startup_license(ctx: typer.Context) -> None:
    """Validate license and check for critical updates."""
    command = _get_invoked_command(ctx)

    # Free commands skip validation
    if command in FREE_COMMANDS or ctx.invoked_subcommand is None:
        return

    # NEW: Check for critical updates
    from src.cli.update_checker import get_update_checker
    checker = get_update_checker()

    if checker.should_block_execution():
        update_info = checker.get_critical_update_info()
        console.print(f"[bold red]CRITICAL UPDATE REQUIRED[/bold red]")
        console.print(f"Current version {update_info.current_version} has critical issues.")
        console.print(f"Please update to {update_info.latest_version} immediately.")
        console.print("\n[cyan]mekong update install[/cyan]\n")
        raise SystemExit(1)

    # Existing license validation...
```

**Success Criteria:**
- [ ] Critical updates block CLI execution
- [ ] Security updates bypass license check (free for all)
- [ ] User sees clear error message with update command

---

### Phase 3: Install and Rollback Commands (1.5h)

**Goal:** Implement `mekong update install` and `mekong update rollback`

**Files to Modify:**
- `src/cli/update_commands.py` - Wire up `update()` and `rollback()` functions
- `src/cli/auto_updater.py` - Fix `rollback()` implementation

**Implementation:**
```python
# In update_commands.py - update() command
@app.command()
def update(
    force: bool = typer.Option(False, "--force", "-f"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Download and install the latest version."""
    from src.cli.auto_updater import get_updater
    from src.lib.raas_gate_validator import get_validator

    updater = get_updater()
    current_version = updater.get_current_version()

    # Check for updates via RaaS Gateway
    from src.cli.update_checker import get_update_checker
    checker = get_update_checker()
    update_info = checker.check_version_sync()

    if not update_info and not force:
        console.print("[bold green]Already on latest version[/bold green]")
        raise typer.Exit(0)

    # RaaS Entitlement Check - Security updates are FREE
    if update_info and not update_info.is_security_update:
        validator = get_validator()
        is_valid, error = validator.validate()

        if not is_valid:
            console.print(Panel(
                "[red]RaaS License Required[/red]\n\n"
                "Non-security updates require a valid RaaS license.\n"
                f"Current: {current_version} | Available: {update_info.latest_version}",
                title="License Check Failed",
                border_style="red",
            ))
            raise typer.Exit(1)

    # Show update info
    if update_info:
        console.print(Panel.fit(
            f"[bold]Update Available[/bold]\n\n"
            f"Current:  {current_version}\n"
            f"Latest:   {update_info.latest_version}\n"
            f"Critical: {'Yes' if update_info.is_critical else 'No'}\n"
            f"Security: {'Yes' if update_info.is_security_update else 'No'}",
            border_style="red" if update_info.is_critical else "green",
        ))

    # Confirmation
    if not yes:
        proceed = typer.confirm("\nProceed with update?")
        if not proceed:
            console.print("[yellow]Update cancelled[/yellow]")
            raise typer.Exit(0)

    # Perform update
    console.print("\n[bold]Downloading update...[/bold]")
    result = updater.update(force=force)

    if result.success:
        console.print(Panel(
            f"[bold green]Update Successful![/bold green]\n\n"
            f"Updated from {result.old_version} to {result.new_version}",
            title="Update Complete",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]Update Failed[/bold red]\n\n{result.message}",
            title="Update Error",
            border_style="red",
        ))
        raise typer.Exit(1)


@app.command()
def rollback() -> None:
    """Rollback to previous version."""
    from src.cli.auto_updater import get_updater

    updater = get_updater()

    console.print("[bold]Rolling back to previous version...[/bold]")
    result = updater.rollback()

    if result:
        console.print("[bold green]Rollback successful![/bold green]")
    else:
        console.print("[bold red]Rollback failed[/bold red]")
        console.print("[dim]No previous version available[/dim]")
        raise typer.Exit(1)
```

```python
# In auto_updater.py - Add rollback implementation
class AutoUpdater:
    # ... existing code ...

    def rollback(self) -> bool:
        """Rollback to previous version."""
        # Read previous version from cache
        cache_path = Path("~/.mekong/update_history.json").expanduser()
        if not cache_path.exists():
            return False

        with open(cache_path, "r") as f:
            history = json.load(f)

        previous_version = history.get("previous_version")
        if not previous_version:
            return False

        # Reinstall previous version via pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", f"mekong-cli=={previous_version}", "--quiet"],
            capture_output=True,
        )
        return result.returncode == 0
```

**Success Criteria:**
- [ ] `mekong update install` downloads and installs update
- [ ] `mekong update rollback` reverts to previous version
- [ ] Config preserved during update
- [ ] License check bypassed for security updates

---

### Phase 4: Status Command (0.5h)

**Goal:** Add `mekong update status` command

**Files to Modify:**
- `src/cli/update_commands.py` - Add `status()` command

**Implementation:**
```python
@app.command()
def status() -> None:
    """Show current update status."""
    from src.cli.update_checker import get_update_checker
    from src.cli.auto_updater import get_updater

    checker = get_update_checker()
    updater = get_updater()

    current_version = updater.get_current_version()

    table = Table(title="Update Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Current Version", current_version)
    table.add_row("Auto-Update Check", "Enabled" if not os.getenv("MEKONG_NO_UPDATE_CHECK") else "Disabled")

    # Check cache status
    cache_status = checker.get_cache_status()
    table.add_row("Last Check", cache_status.get("checked_at", "Never"))
    table.add_row("Cache Status", "Expired" if cache_status.get("is_expired") else "Valid")

    # Check for critical updates
    critical_update = checker.check_critical_update()
    if critical_update:
        table.add_row(
            "Critical Update",
            f"[red]{critical_update.latest_version} (REQUIRED)[/red]",
        )
    else:
        table.add_row("Critical Update", "None")

    console.print(table)
```

**Success Criteria:**
- [ ] `mekong update status` shows current version and cache state
- [ ] Shows if critical update pending
- [ ] Shows auto-update check status

---

### Phase 5: Tests (2h)

**Goal:** Write comprehensive tests for update system

**Files to Create:**
- `tests/cli/test_update_checker.py`
- `tests/cli/test_auto_updater.py`
- `tests/cli/test_update_commands.py`

**Test Cases:**

```python
# tests/cli/test_update_checker.py
class TestUpdateChecker:
    """Test update checker functionality."""

    def test_check_version_returns_none_when_current(self):
        """Should return None when already on latest version."""
        ...

    def test_check_version_returns_update_available(self):
        """Should return UpdateAvailable when newer version exists."""
        ...

    def test_check_version_handles_gateway_timeout(self):
        """Should fail silently on gateway timeout."""
        ...

    def test_critical_update_detection(self):
        """Should detect critical updates from gateway response."""
        ...

    def test_cache_prevents_redundant_checks(self):
        """Should use cached result within 24h TTL."""
        ...

    def test_should_block_execution_for_critical(self):
        """Should block execution for critical updates."""
        ...


# tests/cli/test_auto_updater.py
class TestAutoUpdater:
    """Test auto updater functionality."""

    def test_get_current_version(self):
        """Should return current installed version."""
        ...

    def test_update_preserves_config(self):
        """Should preserve user config during update."""
        ...

    def test_rollback_reverts_version(self):
        """Should rollback to previous version."""
        ...

    def test_checksum_verification(self):
        """Should verify SHA256 checksum."""
        ...


# tests/cli/test_update_commands.py
class TestUpdateCommands:
    """Test update CLI commands."""

    def test_update_check_command(self):
        """Should show update check info."""
        ...

    def test_update_install_command(self):
        """Should install update."""
        ...

    def test_update_rollback_command(self):
        """Should rollback update."""
        ...

    def test_update_status_command(self):
        """Should show update status."""
        ...
```

**Success Criteria:**
- [ ] All tests pass
- [ ] Test coverage > 80%
- [ ] Tests run in < 30s

---

## Implementation Steps Summary

| Step | Description | Effort | Status |
|------|-------------|--------|--------|
| 1 | Update `update_checker.py` to use RaaS Gateway | 1h | pending |
| 2 | Add critical update enforcement in `main.py` | 1h | pending |
| 3 | Implement `update install` command | 1h | pending |
| 4 | Implement `update rollback` command | 0.5h | pending |
| 5 | Add `update status` command | 0.5h | pending |
| 6 | Write unit tests | 2h | pending |

---

## Success Criteria

- [ ] `mekong update check` shows version from RaaS Gateway
- [ ] `mekong update install` downloads and installs update
- [ ] `mekong update rollback` reverts to previous version
- [ ] `mekong update status` shows current state
- [ ] Critical updates block CLI execution
- [ ] Security updates bypass license check
- [ ] Startup check runs async (non-blocking)
- [ ] `MEKONG_NO_UPDATE_CHECK=1` disables check
- [ ] Usage events logged to Phase 4 tracker
- [ ] All tests pass (62 existing + new tests)

---

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gateway unreachable | Update check fails | Fallback to GitHub Releases API |
| Critical update blocks valid CLI | User locked out | Add `--skip-update-check` flag for emergencies |
| Update breaks CLI | Can't rollback | Atomic install with backup, pip-based rollback |
| Rate limit on gateway | Check fails | 24h cache prevents redundant checks |
| Config lost during update | User data loss | Backup/restore config before/after update |

---

## Unresolved Questions

1. Should signature validation use GPG or Ed25519? (Current code has GPG stub but no key)
2. What constitutes a "critical" update? (Semver breaking change? Security CVE?)
3. Should `--skip-update-check` flag be added for emergency bypass?
4. How to handle updates when pip is not available (e.g., system Python)?

---

## Related Files

**Existing:**
- `src/cli/update_checker.py` - Version checking with RaaS Gateway
- `src/cli/auto_updater.py` - Download and install logic
- `src/cli/update_commands.py` - CLI commands
- `src/main.py` - Startup integration
- `apps/raas-gateway/src/cli-version-handler.js` - Gateway endpoint
- `apps/raas-gateway/index.js` - Route registration

**To Create:**
- `tests/cli/test_update_checker.py`
- `tests/cli/test_auto_updater.py`
- `tests/cli/test_update_commands.py`

---

## Next Steps

1. Read existing `update_checker.py` implementation (DONE)
2. Implement Phase 1: RaaS Gateway integration
3. Implement Phase 2: Critical enforcement
4. Implement Phase 3-4: Commands
5. Implement Phase 5: Tests
6. Run test suite + validation
