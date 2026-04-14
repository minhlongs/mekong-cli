# Code Review: Engine Farm A/B Test Migration

**Date:** 2026-04-04
**Reviewer:** code-reviewer agent
**Score:** 7.5/10

## Scope

- Files: 7 (config.env, migrate-models.sh, ab-test.sh, cutover.sh, start-farm.sh, env.ts, package.json)
- LOC: ~375
- Focus: Shell security, model name consistency, error handling, host addressing

## Overall Assessment

Well-structured migration suite with clear phased approach (migrate -> A/B test -> cutover). Model names consistent across config.env, env.ts, and all shell scripts. No hardcoded secrets. Several shell robustness issues and one cross-layer config drift need attention.

---

## Critical Issues

### 1. Rust orchestrator config.rs has STALE default model names

**File:** `/Users/macbookprom1/mekong-cli/ide-core/orchestrator/src/config.rs` (line 38-40)

```rust
router_model: env_str("ROUTER_MODEL", "gemma-4-26b-a4b"),      // OLD
reasoning_model: env_str("REASONING_MODEL", "deepseek-r1-32b"), // OLD
audit_model: env_str("AUDIT_MODEL", "qwen2.5-coder-7b"),        // close but format differs
```

Post-migration models are `qwen2.5-coder:7b`, `qwen3:8b`, etc. Config.rs defaults still reference the OLD models that cutover.sh removes. If env vars are unset, Rust orchestrator silently falls back to non-existent models.

**Fix:** Update defaults to match config.env:
```rust
router_model: env_str("ROUTER_MODEL", "qwen2.5-coder:7b"),
reasoning_model: env_str("REASONING_MODEL", "qwen3:8b"),
audit_model: env_str("AUDIT_MODEL", "qwen3:1.7b"),
```

### 2. migrate-models.sh pipes curl to sh (line 30)

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Standard Ollama install pattern but still a pipe-to-shell. On a production machine, a MITM or DNS hijack executes arbitrary code as current user.

**Risk:** Medium (mitigated by `-fsSL` flags and HTTPS, but worth noting).

**Suggestion:** Add a hash verification or at minimum a confirmation prompt before auto-updating.

### 3. migrate-models.sh leaks SSH credentials in comment (line 6)

```bash
#   or SSH: sshpass -p '    ' ssh macbook@192.168.11.111 'bash -s' < migrate-models.sh
```

Contains internal IP `192.168.11.111`, username `macbook`, and a placeholder for sshpass password. The password field is blank spaces but the pattern encourages filling it in. This is in a public repo.

**Fix:** Remove or redact to:
```bash
#   or SSH: ssh user@host 'bash -s' < migrate-models.sh
```

---

## High Priority

### 4. ab-test.sh: Shell injection via Python f-string interpolation (lines 39-41)

```bash
local duration=$(python3 -c "print(f'{${end_time} - ${start_time}:.2f}')")
local tok_per_sec=$(python3 -c "t=${tokens}; d=${duration}; ...")
```

Shell variables `$end_time`, `$start_time`, `$tokens`, `$duration` are interpolated directly into Python code. If `curl` returns malformed JSON and `python3` outputs unexpected characters, these expand unsanitized into a `python3 -c` invocation.

Current risk is LOW (values come from controlled `time.time()` and JSON parsing with fallback), but the pattern is fragile.

**Fix:** Pass values as arguments:
```bash
local duration=$(python3 -c "import sys; print(f'{float(sys.argv[1]) - float(sys.argv[2]):.2f}')" "$end_time" "$start_time")
```

### 5. start-farm.sh: OLLAMA_HOST binding inconsistency (line 29)

```bash
OLLAMA_HOST="${OLLAMA_HOST}" ollama serve >/tmp/mekong-ollama.log 2>&1 &
```

`config.env` sets `OLLAMA_HOST="127.0.0.1"` (IP only, no port). But Ollama's `OLLAMA_HOST` env var expects `host:port` format (e.g., `127.0.0.1:11434`). Passing just `127.0.0.1` may cause Ollama to bind on default port but some versions may error.

**Fix:** Use the full bind address:
```bash
OLLAMA_HOST="${OLLAMA_HOST}:${OLLAMA_PORT}" ollama serve ...
```

### 6. start-farm.sh does NOT warm TRADING_MODEL and EMBED_MODEL (lines 108-111)

```bash
warm_model "$ROUTER_MODEL"
warm_model "$REASONING_MODEL"
warm_model "$TOOL_MODEL"
# TRADING_MODEL and EMBED_MODEL are NOT warmed
```

Only 3 of 5 models are warmed. First request to trading/embed will hit cold-start latency.

**Fix:** Add:
```bash
warm_model "$TRADING_MODEL"
warm_model "$EMBED_MODEL"
```

---

## Medium Priority

### 7. Version comparison uses lexicographic ordering (migrate-models.sh:28)

```bash
if [[ "$OLLAMA_VERSION" < "0.19" ]]; then
```

String comparison: `"0.9" > "0.19"` is TRUE (lexicographic). If Ollama ever reaches version `0.9x`, this breaks.

**Fix:** Use numeric comparison or `sort -V`:
```bash
if ! printf '%s\n' "0.19" "$OLLAMA_VERSION" | sort -V | head -1 | grep -q "0.19"; then
```

### 8. DEV and PROD models are identical (config.env:11-22, env.ts:27-41)

Both environments use the exact same model set. The env/mode abstraction adds complexity with zero differentiation. If intentional as placeholder for future divergence, add a comment.

### 9. cutover.sh grep pattern for old models is fragile (line 31)

```bash
if "$OLLAMA_BIN" ps 2>/dev/null | grep -q "${model}"; then
```

Model name like `qwen2.5:7b` could match `qwen2.5:7b-q4` or similar substring. Use anchored match or exact column match.

### 10. ab-test.sh results dir created relative to CWD (line 17)

```bash
RESULTS_DIR="ab-test-results-$(date +%Y%m%d-%H%M%S)"
```

If run from different directories, results scatter. Consider using `SCRIPT_DIR` pattern like start-farm.sh does.

---

## Low Priority

- `warm_model()` in start-farm.sh silently swallows failures (`|| true` on line 65) -- acceptable for startup but worth logging
- No `shellcheck` annotations; scripts would benefit from `# shellcheck disable=SC2086` where intentional
- ab-test.sh hardcodes `python3` dependency without checking availability
- config.env `OLLAMA_API` uses variable expansion that only works when sourced, not when read by non-shell tools

---

## Positive Observations

- Consistent use of `set -euo pipefail` across all scripts
- Clean separation: config.env (data), scripts (behavior), env.ts (TypeScript bridge)
- `OLLAMA_BIN` fallback pattern handles non-standard installs
- cutover.sh has `--yes` flag for automation and interactive confirmation for manual runs
- TypeScript env.ts uses `??=` for non-destructive env setup -- respects explicit overrides
- Model names are consistent across config.env, migrate-models.sh, ab-test.sh, cutover.sh, and env.ts (5/5 match)
- Memory budget documentation is helpful

---

## Recommended Actions (Priority Order)

1. **Update config.rs defaults** to match post-migration models (CRITICAL -- silent fallback to deleted models)
2. **Remove SSH credentials comment** from migrate-models.sh (security hygiene for public repo)
3. **Pass shell vars as args** to python3 in ab-test.sh (defense in depth)
4. **Warm all 5 models** in start-farm.sh
5. **Fix OLLAMA_HOST format** to include port for ollama serve
6. **Fix version comparison** to handle numeric edge cases

## Metrics

- Type Coverage (env.ts): 100% -- all exports typed, `as const` used
- Shell Safety: 4/4 scripts use `set -euo pipefail`
- Model Consistency: 5/7 files aligned (config.rs outlier)
- Secret Exposure: 1 issue (SSH comment pattern in migrate-models.sh)

## Verdict: COMMENT

No blocking security vulnerabilities. The config.rs drift is the highest-risk item -- should be fixed before cutover.sh removes old models. Remaining issues are robustness improvements.
