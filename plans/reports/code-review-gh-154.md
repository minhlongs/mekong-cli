# Code Review Report — Issue #154 (`chore/hardening-g2-scanners-and-cli-groups`)

## Round-2 Verification Summary (APPROVED — 0 Blocking Findings)

### Scope (Round 2)
- **Branch**: `chore/hardening-g2-scanners-and-cli-groups`
- **Files Reviewed**: 40 modified files (`+435 / -119` LOC) + 1 untracked test module (`tests/unit/test_g2_security_hardening.py`, `92 LOC`) = 41 files (`+527 / -119` LOC total)
- **Verdict**: **APPROVED** (`0` Critical, `0` High, `0` Medium, `3` Low non-blocking notes)

### Round-2 Acceptance Criteria & Prior Finding Resolution

| # | Criterion / Round-1 Finding | Round-1 | Round-2 | Verification Evidence |
|---|-----------------------------|---------|---------|-----------------------|
| 1 | **Round-1 C1**: `HeartbeatScheduler._parse_tier1_chain` / `_run_tier1_chain` (`src/daemon/heartbeat_scheduler.py:251-361`) | FAIL | **PASS** | Zero `shell=True`. Tokenizes via `shlex.shlex(..., posix=True, punctuation_chars=";&\|<>")` with `whitespace_split=True`; supports safe `&&` and `\|` argv pipelines via `subprocess.run(..., shell=False, input=input_text)`; rejects empty/multiline strings, unclosed quotes, `;`, `\|\|`, `&`, redirections (`<`, `>`, `>>`, `<<`, `<>`, `\|&`), command substitution (`$()`, `` ` ``, `${}`), `python -c` / `node -e`, and destructive binaries (`STRICT_MODE_COMMANDS`). Verified across 49 tests in `tests/test_daemon_health.py` + adversarial probe. |
| 2 | **Round-1 H1 & H2**: `gates.yml` (`lines 142-175`), `ai-native-ci.yml` (`lines 33-34, 80-82`), `requirements.txt`, `pyproject.toml` | FAIL | **PASS** | `gates.yml` installs `requirements.txt` into `$RUNNER_TEMP/trivy-venv`, writes `pip freeze --exclude-editable` to `$RUNNER_TEMP/trivy-deps/requirements.txt`, asserts `pkg_count >= 30`, runs blocking `pip-audit -r`, and scans `${{ runner.temp }}/trivy-deps` via `aquasecurity/trivy-action@v0.36.0` (`refs/tags/v0.36.0` verified upstream) with `exit-code: "1"`. `ai-native-ci.yml` runs blocking `bandit` (no `--exit-zero`) and blocking `pip-audit` (no `\|\| echo`). Unused vulnerable `python-jose` removed from `requirements.txt` and `pyproject.toml`. Semgrep uses deterministic `--config=p/python --config=p/secrets src/ --severity=ERROR --error`. |
| 3 | **Round-1 H3**: `CodeEvolutionEngine._git_cmd` (`src/core/code_evolution.py:12, 273-351, 441-455`) | FAIL | **PASS** | `from __future__ import annotations` added at line 12 (Python 3.9 safe). All git mutations (`checkout -b`, `add -A`, `commit -m`, `merge --`) pass explicit `List[str]` argv vectors with `shell=False` and `check=True`, setting `EvolutionStatus.PASSED` only after `git add` + `git commit` succeed. Verified against quotes, truncation, and `--author` flag smuggling in `tests/test_code_evolution.py:127-170` (`15 passed`). |
| 4 | **Round-1 M1, M2, L7 + Semgrep XML/docs & Core DNA**: `.env.example`, `vietqr_verifier.py`, `pev_swarm_bridge.py`, `package_build*.py`, `docs.py`, `dna/core-dna.json`, `developer.py` | WARN | **PASS** | `.env.example` + `src/services/vietqr_verifier.py:88-90` support both `MEKONG_VIETQR_WEBHOOK_SECRET` and `VIETQR_WEBHOOK_SECRET` while failing closed when unset. `PEVSwarmBridge` (`src/core/pev_swarm_bridge.py:43-46, 1468-1498`) enforces `CommandSanitizer(strict_mode=True)`, strips leading `KEY=VAL` overrides into `env`, and enforces `_ALLOWED_TEST_RUNNERS` with `shell=False`. `parse_safe_xml_root` (`src/command_fabric/package_build_editor_verifiers.py:13-19`) rejects `<!DOCTYPE` / `<!ENTITY` before `ET.fromstring`. `publish_to_custom` (`src/commands/docs.py:410-430`) confines script and source via `.resolve()` + `is_relative_to(workspace_root)` and invokes `["bash", "--", ...]` with `shell=False`; `dna/core-dna.json:318-325` records PR #156 review (`CoreDnaManifest.load()` + `tests/test_core_dna*.py` green). `src/seed/agents/developer.py:13, 59` honors `OUTPUTS_DIR` env override and `mode=0o700`. |
| 5 | **Hard Repo Invariants**: `phase_559_opencore_25_step_catalog.py`, `.mekong/company.json`, `<= 185 LOC` ceilings, `ruff`, `bandit`, clean `/tmp` | PASS | **PASS** | `src/core/opencore/phase_559_opencore_25_step_catalog.py` and `.mekong/company.json` have `0` diff lines against both `HEAD` and `main`. All 33 ceiling-governed files (`src/opc/**/*.py`, `src/core/opencore/*.py`, `src/core/raas_license_verifier.py`, `tests/test_github_content_25_step_sync.py`) are `<= 185 LOC` (max `185 LOC` at `src/opc/connectors/zalo_http.py`, `0` violations). `ruff check src/ tests/` and both `bandit` gates pass with `0` errors. Zero leftover temp processes or `/tmp` venvs. |

---

### Low Priority / Non-Blocking Notes (Round 2)

1. **[LOW] Path-qualified binary check in `HeartbeatScheduler._parse_tier1_chain`**
   - **Location**: `/Users/macbook/mekong-cli-atoz-strategy-e/src/daemon/heartbeat_scheduler.py:307`
   - **Detail**: `if argv[0] in sanitizer.STRICT_MODE_COMMANDS:` compares the raw token rather than `Path(argv[0]).name`, so a path-qualified binary with a relative path target (e.g. `/bin/rm foo.txt` or `/bin/dd if=/dev/zero of=foo`) is not matched by `STRICT_MODE_COMMANDS` (whereas `/bin/rm -rf /...` is still caught by `DANGEROUS_PATTERNS`). Non-blocking because Tier 1 loop commands originate from local owner-controlled `.mekong/loops/*.json` and `HEARTBEAT.md` files; optional defense-in-depth is `Path(argv[0]).name in sanitizer.STRICT_MODE_COMMANDS`.

2. **[LOW] Orphaned legacy `engine/license/jwt_license_generator.py` still imports `jose`**
   - **Location**: `/Users/macbook/mekong-cli-atoz-strategy-e/engine/license/jwt_license_generator.py:21` (lazy-imported by `/Users/macbook/mekong-cli-atoz-strategy-e/src/services/license_enforcement.py:133, 198` only when `license_key.startswith("raasjwt-")`)
   - **Detail**: Removing `python-jose` from `requirements.txt` and `pyproject.toml` is safe for all active runtime paths and CI workflows because canonical JWT auth (`src/middleware/license_gate.py`, `src/services/admin_token_service.py`) uses `pyjwt>=2.8.0` and canonical offline license verification uses `src/core/raas_license_verifier.py`; `LicenseEnforcementService` has zero production callers in `src/` and its legacy root-level test files (`tests/test_jwt_license.py`, `tests/test_license_enforcement.py`) are outside CI's curated suite. A follow-up cleanup can migrate `jwt_license_generator.py` to `pyjwt` (or remove the orphaned ROIaaS Phase 4/7 modules and stale `Makefile:116` / `poetry.lock` `python-jose` references).

3. **[LOW] Carry-over from Round-1 L8: `zalo_http._stdlib_http_post` initial-URL `https://` check**
   - **Location**: `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/connectors/zalo_http.py:71-75`
   - **Detail**: Enforces `https://` on the initial request URL while keeping `zalo_http.py` at the `185 LOC` ceiling (`185 LOC`). Low risk since production default `ZALO_OA_CS_ENDPOINT` is `https://openapi.zalo.me/v3.0/oa/message/cs`.

---

### Round-2 Metrics & Verification Checks Executed

- **Ruff Lint (`python3 -m ruff check src/ tests/`)**: PASS (`All checks passed!`)
- **Bandit Gate 1 (`python3 -m bandit -r src/ -lll -q`)**: PASS (`0` High findings)
- **Bandit Gate 2 (`python3 -m bandit -r src/opc/ src/core/opencore/ src/core/raas_license_verifier.py src/seed/ integrations/ -ll -q`)**: PASS (`0` Medium/High findings)
- **Workflow YAML Validation (`.github/workflows/gates.yml`, `.github/workflows/ai-native-ci.yml`)**: PASS + upstream tag `aquasecurity/trivy-action@v0.36.0` verified (`a9c7b0f06e461e9d4b4d1711f154ee024b8d7ab8`)
- **Core DNA Gate (`CoreDnaManifest.load()` + `tests/test_core_dna.py` + `tests/test_core_dna_workflow.py`)**: PASS (`13 passed`)
- **CLI Group Count (`len(build_app().registered_groups)`)**: PASS (`189`)
- **Pytest Suites Executed**: `606 passed` across:
  - `tests/test_daemon_health.py` (`49 passed`, including new `TestHeartbeatSchedulerExecuteTask`)
  - `tests/test_code_evolution.py` (`15 passed`, including quotes & `--author` flag-smuggling git test)
  - `tests/test_antigravity_pev_swarm.py -k "not test_antigravity_healthcheck_clean"` (`32 passed`, including `KEY=VAL` env prefix & `python3 -c` block test; note `test_antigravity_healthcheck_clean` expects gitignored `.agents/skills` absent in isolated worktrees)
  - `tests/unit/test_g2_security_hardening.py` (`4 passed`: XXE guard, editor verifiers, workspace-confined `publish_to_custom`, VietQR legacy/prefixed env fallback)
  - OpenCore 25-Step & RaaS Boundary Gate suites (`61 passed`)
  - `tests/seed/`, `tests/commands/`, `tests/unit/`, `tests/daemon/`, OPC & Strategy E suites (`432 passed`)
- **LOC & Immutability Invariants**:
  - `33` files checked across `src/opc/**/*.py`, `src/core/opencore/*.py`, `src/core/raas_license_verifier.py` (`169 LOC`), and `tests/test_github_content_25_step_sync.py` (`151 LOC`): max `185 LOC`, `0` violations
  - `src/core/opencore/phase_559_opencore_25_step_catalog.py`: `0` diff lines
  - `.mekong/company.json`: `0` diff lines
  - `/tmp` temporary scanner venvs / orphan processes: `0` found

---

## Round-1 Historical Review Record (Superseded by Round-2 Fixes Above)

### Round-1 Summary
- **Scope**: 30 modified files (`+110 / -84` LOC)
- **Round-1 Verdict**: Changes Requested (`1` Critical, `3` High, `2` Medium, `2` Low)
  - **C1 (RESOLVED in Round 2)**: `HeartbeatScheduler.execute_task` used `src.security.command_sanitizer` + `shell=True`, breaking valid `&&`/`|` recipes and permitting multiline unclosed-quote bypass.
  - **H1 (RESOLVED in Round 2)**: `gates.yml` Trivy scanned unpinned `requirements.txt` (`0` `==` pins) and used mutable `@master`.
  - **H2 (RESOLVED in Round 2)**: `gates.yml` Semgrep used untested `--config=auto` instead of deterministic ruleset with triaged findings.
  - **H3 (RESOLVED in Round 2)**: `CodeEvolutionEngine._git_cmd` lacked `from __future__ import annotations` and interpolated `attempt.description[:50]` inside shell-parsed quotes.
  - **M1 (RESOLVED in Round 2)**: `.env.example` `VIETQR_WEBHOOK_SECRET` vs `vietqr_verifier.py` `MEKONG_VIETQR_WEBHOOK_SECRET` mismatch.
  - **M2 (RESOLVED in Round 2)**: `PEVSwarmBridge.verify_task` `test_command` lacked `KEY=VAL` prefix support, `CommandSanitizer(strict_mode=True)`, and `_ALLOWED_TEST_RUNNERS`.
  - **L7 (RESOLVED in Round 2)**: `src/seed/agents/developer.py` now reads `OUTPUTS_DIR` from env and passes `mode=0o700` to `os.makedirs`.
