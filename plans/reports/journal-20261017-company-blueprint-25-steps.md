# Company Blueprint & 25-Step Open-Core Synchronization

**Date**: 2026-10-17 19:30
**Severity**: High
**Component**: Open-Core Blueprint & Company Governance Ledger (`.mekong/company.json`)
**Status**: Resolved

## What Happened

While synchronizing the company blueprint with the 25-step Open-Core catalog (`phase_559_opencore_25_step_catalog.py`), we discovered that `.mekong/company.json` had ballooned to 3,157 lines due to 444 duplicate synthetic test revenue events (`polar_evt_endpoint_001` / `polar_evt_duplicate`). This completely violated our core governance invariant: *"No synthetic revenue events is traction."* 

We executed `/ak-bootstrap plans/company-blueprint/tasks.md`, thoroughly purged all synthetic revenue entries, rebuilt the blueprint files to strictly align with the 25-step catalog, and added a dedicated verification suite.

## The Brutal Truth

This was infuriating. We let test pollution slip directly into production metadata artifacts, turning `.mekong/company.json` into a garbage dump of 444 fake billing events. It's a glaring reminder that if you don't aggressively validate state invariants in CI, mock clutter will silently corrupt your source of truth. We spent hours cleaning up self-inflicted data bloat instead of building features.

## Technical Details

- **File Bloat**: `.mekong/company.json` reached 3,157 lines with 444 duplicate `polar_evt_*` revenue objects.
- **Error Condition**: Diagnostic assertion `len(company_data["revenue_events"]) == 0` failed repeatedly during sync checks.
- **Modules Shipped**:
  - `plans/company-blueprint/tasks.md` (117 LOC)
  - `plans/company-blueprint/plan.md` (47 LOC)
  - `.mekong/company.json` (65 LOC, scrubbed)
  - `opencore_saas_restructuring_command.py` (`blueprint` subcommand, 120 LOC)
  - `tests/test_company_blueprint_sync.py` (116 LOC)

## What We Tried

Initially attempted to filter events dynamically at runtime in the sync command, but that left the underlying JSON file corrupted and bloated on disk. We ultimately took the correct hard route: stripped out all fake revenue payloads entirely, rewrote the company ledger schema contract to reject synthetic test IDs at the validation layer, and enforced zero tolerance for non-empty revenue arrays in offline blueprints.

## Root Cause Analysis

Lazy test setup. Test suites were writing mock revenue payloads directly into the live `.mekong/company.json` state store without cleanup fixtures or isolation boundaries.

## Lessons Learned

Never allow test fixtures to write directly to persistent production configuration files without immediate teardown or explicit in-memory isolation. A state store is not a scratchpad.

## Next Steps

- **Action**: Enforce pre-commit hook validation to block any `.mekong/company.json` commits containing `polar_evt` substrings.
- **Owner**: Core Engineering / DevOps.
- **Timeline**: Completed immediately (SHA 23b4cb1).
