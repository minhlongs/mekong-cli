---
title: Phase 01 Seed Foundation — Code Review
scope: seed/, tools/
reviewer: code-reviewer
date: 2026-04-25
score: 7.5/10
---

## Scope

- Files: seed/config.py, seed/llm_client.py, seed/memory.py, seed/agents/base.py, seed/agents/ceo.py, seed/agents/developer.py, seed/agents/tester.py, seed/__init__.py, seed/main.py, tools/__init__.py, tools/file_system.py, tools/browser.py
- LOC: ~370 across 12 files (all under 200-line limit — compliant)
- E2E passed: python3 seed/main.py "Tạo một trang HTML..." → outputs/index.html

## Overall Assessment

Clean, minimal implementation that respects KISS/YAGNI. No syntax errors detected. Logic is correct for the seed scope. Three issues need action: one high (shell injection), one medium (broken import in __init__.py), one medium (SQLite connection never closed). Remaining items are low/informational.

---

## Critical Issues

None.

---

## High Priority

### H1: Shell Injection in execute_command (tools/file_system.py:26-27)

`shell=True` with raw `cmd: str` passed directly from LLM output → arbitrary code execution if LLM is prompted to run malicious commands.

```python
# Current — UNSAFE when cmd comes from LLM
result = subprocess.run(cmd, shell=True, ...)

# Fix — use list form, reject if cmd contains shell metacharacters
import shlex
result = subprocess.run(shlex.split(cmd), shell=False, ...)
```

At seed scope, `execute_command` is exported but not called by DeveloperAgent (which only calls `_save_file`). Risk is latent but real if any future agent invokes this tool with LLM-generated input. Fix before Phase 02.

---

## Medium Priority

### M1: Broken Import — TesterAgent in seed/agents/__init__.py

`seed/agents/__init__.py` imports `TesterAgent` from `.tester`, and `tester.py` exists. However, `seed/__init__.py` does NOT export `TesterAgent` and `seed/main.py` never instantiates it. The `__init__.py` import is fine at module level, but the agent is unused dead weight — borderline YAGNI violation.

Action: either wire TesterAgent into main.py verify step or remove from `__init__.py` exports to keep seed minimal.

### M2: SQLite Connection Never Closed (seed/memory.py)

`SeedMemory._sql` is a `sqlite3.connect()` opened in `__init__` and never closed. The singleton means it lives for the process lifetime — acceptable for CLI scripts, but if the process is embedded (e.g., imported as a library), the connection leaks.

```python
def close(self) -> None:
    self._sql.close()
```

Add `close()` and call it in `main.py` via `try/finally` or `atexit`. Low urgency for CLI-only use.

### M3: Path Traversal Partial Fix (seed/agents/developer.py:58)

`Path(file_path).name` strips directory components — correct. But it does NOT prevent overwriting existing files in OUTPUTS_DIR (e.g., `index.html` written twice silently overwrites). Not a traversal risk, but silent destructive overwrites from LLM-generated paths could lose work.

```python
# Add collision check
if full_path.exists():
    stem = full_path.stem
    suffix = full_path.suffix
    full_path = out_dir / f"{stem}_{uuid.uuid4().hex[:6]}{suffix}"
```

---

## Low Priority

### L1: Singleton Mutation Side Effect (seed/agents/base.py:22-23)

```python
self.llm = get_llm_client()  # singleton
if model:
    self.llm.model = model   # MUTATES the shared singleton
```

If a second agent is instantiated with a different model after the first, the singleton's model is permanently changed for all subsequent agents. In current code only one model is used, so no bug — but fragile.

Fix: `self.llm = LLMClient(model=model)` when model override needed (shallow copy, not singleton mutation).

### L2: print() Statements Instead of Logging (seed/main.py, ceo.py, developer.py)

Multiple `print(f"  🤖 CEO analyzing...")` scattered across agents. These bypass the logging framework configured in each module (`logger = logging.getLogger(__name__)`). Makes log-level control impossible.

Acceptable for seed/demo phase, but should be replaced before Phase 02 production wiring.

### L3: Memory Truncation May Lose Context (seed/agents/base.py:73-76)

```python
f"Task: {task[:200]}...\nResponse: {response[:500]}..."
```

The hardcoded `...` suffix is appended even when the content is NOT truncated (e.g., task < 200 chars). Cosmetic but misleading in memory storage.

```python
task_stored = task if len(task) <= 200 else task[:200] + "..."
```

### L4: browse_website — No URL Validation (tools/browser.py:12)

Accepts any URL string including `file://` and `ftp://`. For seed this is low risk (no agent invokes it yet), but worth adding a scheme allowlist:

```python
if not url.startswith(("http://", "https://")):
    return "[browse_website error: only http/https allowed]"
```

### L5: Hardcoded Emoji in main.py

Emoji in `print()` calls will render correctly in most terminals but may break CI log parsers or Windows cmd. Low priority, style-only.

---

## Positive Observations

- `urllib` stdlib choice: correct for Python 3.14 certifi issue — intentional, well-commented.
- `_post_json` / `_get_json` separation is clean and testable.
- `_parse_response` multi-JSON scanner (reversed positions) is a pragmatic solution to LLM JSON-in-text outputs — good defensive parsing.
- Chroma + SQLite hybrid is appropriate: semantic recall + fast recency without a server.
- `check_same_thread=False` on SQLite is correctly set for potential multi-threaded use.
- All files under 200 lines — compliant with project rules.
- `Path(file_path).name` path traversal mitigation: adequate for seed scope.
- YAGNI respected: no over-engineering, no unused abstractions.

---

## Score: 7.5/10

| Area | Score |
|------|-------|
| Syntax / imports | 9/10 (minor dead import) |
| Security | 6/10 (shell injection latent) |
| Error handling | 8/10 |
| Memory / resource | 7/10 (unclosed SQLite) |
| YAGNI compliance | 9/10 |
| Code clarity | 8/10 |

---

## Recommended Actions (Prioritized)

1. **[H1 — Before Phase 02]** Replace `shell=True` in `execute_command` with `shlex.split` + `shell=False`.
2. **[M1 — Now]** Decide: wire TesterAgent into main.py or remove from `agents/__init__.py`.
3. **[M2 — Phase 02]** Add `SeedMemory.close()` + `atexit` registration in `get_memory()`.
4. **[M3 — Phase 02]** Add filename collision UUID suffix in `_save_file`.
5. **[L1 — Phase 02]** Fix singleton model mutation: instantiate new `LLMClient` for model overrides.
6. **[L2 — Phase 03]** Replace print() with logger.info() throughout agents.
7. **[L4 — Phase 02]** Add URL scheme allowlist in `browse_website`.

---

## Unresolved Questions

1. Is `execute_command` intended to be called by agents via tool-use dispatch in Phase 02? If yes, H1 fix is critical before wiring.
2. TesterAgent: is the verify-loop (CEO → Developer → Tester) planned for Phase 02 main.py, or is Tester a stub for future phases only?
3. `LLM_TIMEOUT=120` applies to chat calls; embed calls use hardcoded `timeout=30`. Should embed timeout also be configurable via env?
4. ChromaDB `PersistentClient` creates `data/chroma/` on first run. Is `data/` in `.gitignore`? (Not checked — worth verifying before first commit.)
