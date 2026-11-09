# Phase 02 — Wire CLI (`mekong opc`) & Domain Handler (`_handle_opc`) + Core DNA Manifest

## Context
- `src/cli/commands/opc_command.py` only exposes `validate-pack`, `proposal`, `decide`, and `status`.
- `decide_proposal` hardcodes `client-proposal-followup/pack.json`, lacks `ZaloSandboxConnector`, and drops `proposal_draft` and `action_payload` when calling `state.save_run(...)`.
- `_handle_opc` in `src/core/cli_domain_handlers.py` only lists packs.
- Changing `src/cli/commands/opc_command.py` triggers `.github/workflows/core-dna-gate.yml`, requiring a corresponding entry in `dna/core-dna.json`.

## Requirements
1. In `src/cli/commands/opc_command.py`:
   - Catch `QuarantineViolationError` in `run_proposal_flow` (`mekong opc proposal`) and exit with `typer.Exit(code=1)`.
   - In `decide_proposal` (`mekong opc decide`), load `run_data = state.get_run(run_id)` first, resolve the pack manifest matching `run_data["pack_id"]` from `src/opc/packs/<pack_id>/pack.json` (falling back to `_DEFAULT_PACK_DIR / "pack.json"`), pass both `MockConnector` and `ZaloSandboxConnector` to `OPCEngine`, catch `ApprovalSecurityError` with `typer.Exit(code=1)`, and preserve `draft_data=run_data.get("proposal_draft")` and `action_payload_data=run_data.get("action_payload")` in every `state.save_run(...)` call.
   - Add `@opc_app.command(name="quarantine")` to inspect text or request files via `QuarantineFloor` (with `--text`, `--source`, `--json`, and non-zero exit when `--enforce` blocks unsafe text).
   - Add `@opc_app.command(name="pilot-a")` to execute the Pilot A Zalo OA → Quarantine → Quote + VietQR → Approval Card vertical slice from CLI (with optional `--approve-and-send`, `--message`, `--db`, `--json`).
   - Add `@opc_app.command(name="bench")` to run all 5 deterministic `MekongBenchRunner` layers and output either the Markdown table or `--json`.
2. In `src/core/cli_domain_handlers.py`:
   - Extend `_handle_opc(params)` so `action = str(params.get("action", "list_packs")).lower()` dispatches `list_packs` (default backward-compatible behavior), `quarantine`, `pilot_a`, and `bench`.
3. In `dna/core-dna.json`:
   - Add the contribution review record for branch `feat/opc-production-callers-and-fourth-doors` so `Core DNA Gate` passes in CI.

## Files
- Modify: `src/cli/commands/opc_command.py`
- Modify: `src/core/cli_domain_handlers.py`
- Modify: `dna/core-dna.json`
- Test: `tests/test_opc_production_callers.py`

## Validation
- `python3 -m pytest tests/test_opc_production_callers.py tests/test_opc_platform_contract.py tests/test_core_dna.py -v`
- `python3 -m ruff check src/ tests/`
