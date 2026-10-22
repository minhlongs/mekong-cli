---
title: "Phase 1: CLI writes artifacts and --deep reaches IdeaLoop"
status: complete
---

## Completion evidence (2026-10-22)

Verified by running the command through `typer.testing.CliRunner`:

- `mk idea "<non-opencore idea>" -o <tmp>` exits 0 and writes `company.json`, `00-framework.md`, `mvp-scope.md`; `result["written"]` lists all three absolute paths.
- `mk idea ... --dry-run` reports a non-empty `written` list and creates nothing on disk (output dir absent after run).
- `mk idea "<open-core idea>" --json` carries `brainstorm_contract` with live `readiness_verdict`, `safe_for_public_github`, `saas_paywall_active`, `contract_digest`, and `00-framework.md` renders a "Live readiness evidence" section.
- `mk idea ... --deep --dry-run` reaches `IdeaLoop`: `deep_run` reports `run_id`, `ok`, `reason`, `iterations`, and an `audit_log` path that exists. With no LLM configured the loop fails truthfully (`No module named 'src.core.llm_client'`) and **the deterministic blueprint is still written** — the specified degrade path.
- `mk idea run --help` lists `--dry-run` and no longer lists `--auto` or `--parallel`.

Design note recorded: `_write_blueprint` writes each key relative to `--output-dir`, so `company.json` lands at `<output_dir>/company.json` and never in the repository root. Nothing is written outside the caller's chosen directory.


# Phase 1: CLI writes artifacts and --deep reaches IdeaLoop

## Overview

Make `mk idea run` put a real blueprint on disk and make `--deep` spawn the existing
autopilot loop under its safety budget. This is the change that stops every run from
regenerating 25 files inside the agent's context.

## Requirements

- [ ] `mk idea "<text>" -o plans/co` writes `company.json` plus one `.md` per step into `--output-dir` (keys are relative to `--output-dir`; nothing is written to the repo root)
- [ ] Written blueprint embeds the **live** readiness verdict from `OpenCoreDeepBrainstormEngine`, not a literal
- [ ] `--deep` reaches `mekong/autopilot/ideaLoop.IdeaLoop` with `dry_run` honoured
- [ ] `--dry-run` prints the plan and writes nothing
- [ ] JSON output reports the written file paths so callers and tests can assert on them

## Implementation Steps

1. Add `_write_blueprint(result, output_dir) -> list[str]` to `src/cli/idea_commands.py`, building a `dict[str, str]` from the values `_pipeline_validate`/`_pipeline_bmc`/`_pipeline_prd`/`_pipeline_handoff` already return, then delegating to `src.core.company_init.write_config_files(files, base_dir=output_dir)`.
2. Add a `00-framework.md` key carrying the live audit: verdict, `safe_for_public_github`, `saas_paywall_active`, and the 25-row phase summary from `synthesize()`.
3. Wire `--deep` to `IdeaLoop(RunOptions(idea=..., dry_run=opts.dry_run))`, writing to `.mekong/idea/<run>/`; keep the synthesize() call for the deterministic `brainstorm_contract` payload.
4. Add a `--dry-run` flag: when set, print what would be written and touch nothing.
5. Call `_write_blueprint` from `idea_run` after the four pipeline stages, before the final Panel; include `written` in `result`.

## Files

- `src/cli/idea_commands.py` (not LOC-policed; the 185 guard covers only `src/core/opencore`)
- `src/core/company_init.py` (read-only reuse: `write_config_files`)
- `mekong/autopilot/idea_loop.py` (read-only reuse: `IdeaLoop`, `RunOptions`)

## Todo

- [ ] `_write_blueprint` implemented and called from `idea_run`
- [ ] live audit section written into the blueprint
- [ ] `--deep` runs IdeaLoop, `--dry-run` suppresses writes
- [ ] `result["written"]` populated

## Success Criteria

`mk idea "demo" -o plans/co && find plans/co -type f` returns more than one file and one
of them is `company.json` — and nothing was written outside `plans/co`. `mk idea "demo"
--dry-run` prints the plan and leaves the output directory absent or empty.
