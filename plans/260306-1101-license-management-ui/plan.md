---
title: "Terminal Interactive License Management UI"
description: "Interactive menu-driven UI for admin license operations with full CRUD support"
status: pending
priority: P2
effort: 4h
branch: master
tags: [license, cli, interactive, admin, raas]
created: 2026-03-06
---

# Terminal Interactive License Management UI

## Overview

Build interactive terminal UI for license management operations using `questionary` for menu navigation and `rich` for formatted output.

## Context Links

- Research: `plans/reports/researcher-260306-1101-license-cli-patterns.md`
- Phase 2 Report: `plans/reports/phase2-license-admin-260306-1045-report.md`
- Existing CLI: `src/commands/license_admin.py`
- Admin Service: `src/api/admin_license_service.py`

## Key Insights

- Existing CLI has basic commands (list, create, revoke, audit, dashboard) but no interactive CRUD menu
- `questionary` already used in project for interactive prompts
- Admin service already provides all CRUD operations
- Pattern: async service methods wrapped with `asyncio.run()` in sync CLI commands

## Requirements

### Functional
- [x] List licenses with filters (tier, status, email, pagination)
- [x] Create license keys (single/bulk)
- [x] Revoke license with reason
- [x] Update license (tier, email, limits)
- [x] View audit logs
- [x] Dashboard with summary stats

### Non-Functional
- Menu-driven navigation
- Input validation at each step
- Error handling with user-friendly messages
- Consistent with existing CLI patterns
- No breaking changes to existing commands

## Component Breakdown

### 1. Menu System (`src/commands/license_admin.py`)
- Main menu loop with clear screen
- Sub-menus for each operation (Create, Revoke, Update, View)
- Dynamic choices based on state
- Graceful exit handling

### 2. Formatters (reuse existing + enhance)
- `get_status_badge()` - colored status indicators
- `format_date()` - consistent date display
- `format_details()` - audit log details
- `format_license_table()` - reusable table builder
- `mask_key()` - security key masking

### 3. CRUD Handlers
- `_handle_list()` - interactive list with filter prompts
- `_handle_create()` - guided form for new keys
- `_handle_revoke()` - revoke with confirmation
- `_handle_update()` - modify existing licenses
- `_handle_audit()` - view audit logs with filters

### 4. Input Validation
- License key format validation
- Email format validation
- Tier selection validation
- Required field checks
- Confirmation prompts for destructive actions

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `src/commands/license_admin.py` | MODIFY | Add interactive CRUD menu system |
| `src/commands/license_admin.py` | ADD | New commands: `update`, interactive CRUD flow |
| `src/api/admin_license_service.py` | ADD | `update_license()` method (if missing) |

## Implementation Steps

### Step 1: Add Update Method to Admin Service
**File:** `src/api/admin_license_service.py`

Add `update_license()` async method:
```python
async def update_license(
    self,
    key_id: str,
    updates: Dict[str, Any],
    updated_by: Optional[str] = None,
    actor_ip: Optional[str] = None,
) -> Dict[str, Any]:
    """Update license properties."""
    # Validate key exists
    # Apply updates via repo.update_license()
    # Log audit entry
```

### Step 2: Add Update Command to CLI
**File:** `src/commands/license_admin.py`

Add `@app.command("update")` function:
- Select license by ID or key pattern
- Interactive form for fields to update
- Confirmation before save
- Audit logging

### Step 3: Build Interactive Menu System
**File:** `src/commands/license_admin.py`

Enhance `interactive_dashboard()` → `interactive_menu()`:

```python
MAIN_MENU_CHOICES = [
    "📋 List Licenses",
    "➕ Create License",
    "✏️  Update License",
    "❌ Revoke License",
    "📜 View Audit Logs",
    "📊 Dashboard Summary",
    "❌ Exit",
]
```

### Step 4: Implement CRUD Handlers

#### `_handle_list()`
- Prompt for filters (tier, status, email)
- Paginated display
- Option to view next/prev page

#### `_handle_create()`
- Prompt for email (required)
- Select tier from dropdown
- Optional: quantity, days, notes
- Display generated keys in panel

#### `_handle_revoke()`
- Prompt for key ID or select from list
- Show current license info
- Require reason
- Confirmation prompt
- Display success/failure

#### `_handle_update()`
- Select license to update
- Show current values
- Prompt for fields to change
- Validate new values
- Confirmation and save

#### `_handle_audit()`
- Prompt for filters (action, date range)
- Display logs in table
- Option to export/view details

### Step 5: Add Input Validators

```python
def validate_email(email: str) -> bool:
    """Validate email format."""

def validate_key_id(key_id: str) -> bool:
    """Validate key ID format."""

def validate_tier(tier: str) -> bool:
    """Validate tier selection."""
```

### Step 6: Error Handling & User Feedback

All handlers use:
- `console.print(Panel(...))` for section headers
- `console.print("[bold red]Error:[/bold red]")` for errors
- `console.print("[bold green]✓[/bold green]")` for success
- `typer.Exit(code=1)` for fatal errors
- Early return on cancel/interrupt

## Todo List

- [ ] Step 1: Add `update_license()` to `admin_license_service.py`
- [ ] Step 2: Add `update` command to `license_admin.py`
- [ ] Step 3: Build main menu loop with questionary
- [ ] Step 4: Implement `_handle_list()` with filters
- [ ] Step 5: Implement `_handle_create()` with form
- [ ] Step 6: Implement `_handle_revoke()` with confirmation
- [ ] Step 7: Implement `_handle_update()` with validation
- [ ] Step 8: Implement `_handle_audit()` with filters
- [ ] Step 9: Add input validators
- [ ] Step 10: Test all flows manually
- [ ] Step 11: Code review with `/review`

## Success Criteria

| Criterion | Verification |
|-----------|--------------|
| Menu displays correctly | `mekong license-admin` shows main menu |
| All CRUD operations work | Create, Read, Update, Revoke via menu |
| Input validation prevents errors | Invalid email/key rejected |
| Error messages are clear | Red panels with actionable info |
| Audit logs capture all actions | Check DB after each operation |
| Consistent with existing patterns | Uses questionary/rich like existing code |
| No breaking changes | Existing commands still work |

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Async/sync pattern issues | Follow existing `asyncio.run()` wrapper pattern |
| Screen flicker on clear | Use `console.clear()` sparingly, only between major sections |
| Input validation gaps | Add validators for all required fields |
| Database connection errors | Wrap all service calls in try/except |

## Security Considerations

- License keys masked in list view: `raas-pro-abc***xyz`
- All admin actions logged to audit_logs
- Actor email and IP recorded for each operation
- Reason required for revocation
- Confirmation required for destructive actions

## Next Steps

After completion:
1. Test all interactive flows manually
2. Add to CLI help documentation
3. Consider web dashboard (Phase 4)

## Unresolved Questions

1. Should update support bulk operations (update multiple licenses)?
2. Should audit logs support CSV export?
3. Should there be a "search by key pattern" feature in list view?
