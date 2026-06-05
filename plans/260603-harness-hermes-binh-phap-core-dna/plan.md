# Harness + Hermes + Binh Phap Core DNA Bootstrap

## Status

- [x] Read README and current harness docs.
- [x] Research source anchors: Fowler harness engineering, Hermes docs.
- [x] Add public Core DNA manifest.
- [x] Add deterministic contribution gate.
- [x] Add CLI status/check command.
- [x] Add tests for manifest and gate.
- [x] Add PR workflow + CODEOWNERS gate.
- [x] Wire Core DNA into `CommandAuthorizer`.
- [x] Add runtime harness control-loop projection.
- [x] Add Binh Phap solo-company operating doctrine.
- [x] Add doctrine validation CLI and tests.
- [x] Add executable harness eval runner.
- [x] Wire executable harness evals into Core DNA PR workflow.
- [x] Add deterministic Core DNA attestation.
- [x] Add Hermes closed learning-loop contract and eval.
- [x] Add reviewed root command-surface manifest and eval.
- [x] Run targeted verification.

## Requirements

- Turn Mekong into harness-engineering platform, not prompt-only CLI.
- Use Hermes ideas: closed loop, skills, memory, MCP-safe extensibility.
- Use Binh Phap as operating compass for solo-company execution.
- Keep source open.
- Lock official core DNA: new features require PR + owner/community review.
- Support `--auto --parallel` direction through declared advanced features.

## Implementation

- Manifest: `dna/core-dna.json`
- Gate: `src/core/core_dna.py`
- Attestation: `src/core/core_dna.py`
- Runtime enforcement: `src/core/command_authorizer.py`
- Harness loop: `src/harness/core/control_loop.py`
- Doctrine: `dna/binh-phap-operating-system.json`
- Doctrine validation: `src/binh_phap/operating_system.py`
- Hermes loop: `dna/hermes-learning-loop.json`
- Hermes validation: `src/harness/learning_loop.py`
- Command surface: `dna/command-surface.json`
- Command-surface validation: `src/core/command_surface.py`
- Harness evals: `src/harness/evals/solo_ceo.py`
- PR gate: `.github/workflows/core-dna-gate.yml`
- CLI: `python3 -m src.main binh-phap dna`
- CLI: `python3 -m src.main binh-phap doctrine`
- CLI: `python3 -m src.main harness-eval`
- Docs: `HARNESS.md`, `docs/harness-engineering.md`, PR template
- Tests: `tests/test_core_dna.py`, `tests/core/test_command_authorizer.py`, `tests/test_binh_phap_operating_system.py`

## Verification

- `python3 -m pytest tests/test_core_dna.py`
- `python3 -m pytest tests/test_binh_phap_operating_system.py tests/test_core_dna.py tests/core/test_command_authorizer.py tests/test_binh_phap_dispatcher.py`
- `python3 -m src.main binh-phap dna --feature cook-auto-parallel`
- `python3 -m src.main binh-phap dna --feature private-local-updater`
- `python3 -m src.main binh-phap doctrine --json`
- `python3 -m src.main harness-eval --json`
- `python3 -m src.main binh-phap dna --attest`
- `python3 -m src.main --help`
- `python3 -m pytest tests/test_core_dna.py tests/test_binh_phap_operating_system.py tests/test_hermes_learning_loop.py tests/test_command_surface.py tests/test_harness_eval.py tests/core/test_command_authorizer.py`

## Verification Notes

- Targeted harness/Core DNA suite: pass, 62 tests.
- Harness eval: pass, 5/5 deterministic evals.
- CLI smoke: pass, `harness-eval` command registered.
- Full `python3 -m pytest tests/`: collection currently fails on legacy missing modules outside this slice: `seed.agents`, `seed.llm_client`, `seed.main`, `seed.memory`, `src.a2ui`, `scripts.contract_gen`, and `integrations.zalo`.

## Unresolved Questions

- Should the legacy seed/a2ui/contract_gen/zalo tests be restored, skipped, or moved behind optional extras?
