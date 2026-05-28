# Implementation Plan: CheetahClaws Optimization

## Objective
Optimize the code generation intelligence of CheetahClaws running with local LLMs (Qwen3.6 35B) to achieve a high coding success rate, targeting Claude-level formatting, logic, and self-correction behavior.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | Benchmark Design (R3) | Create a 5-task coding benchmark suite at `tests/bench_coding.py` or `.cheetahclaws/` | None | DONE |
| 2 | Prompt & Overlay Tuning (R1) | Optimize `prompts/overlays/qwen.md` and default system prompt | None | DONE |
| 3 | Core Engine Self-Correction (R2) | Implement syntax checking & auto-repair hooks in `agent.py` | M1 | DONE |
| 4 | Optimization Iteration & Benchmarking | Run benchmark suite, iterate on prompts and correction logic | M1, M2, M3 | DONE |
| 5 | Validation & Verification | Verify success rate >= 80% and no regressions in other features | M4 | DONE |

## Detailed Implementation Tasks

### 1. Benchmark Design (R3)
- Create `tests/bench_coding.py` with 5 diverse coding tasks:
  1. String manipulation (e.g. converting snake_case to camelCase and vice-versa, handling edge cases).
  2. Markdown table parser (extracting headers and rows into a structured dict).
  3. Regex extraction (extracting emails and domains with validation).
  4. Bug-fix task (a Python file with a logic bug to identify and fix).
  5. Structured output generation (generating a JSON file matching a schema).
- The benchmark script must programmatically run CheetahClaws against each task using local Qwen3.6 execution, check the generated output, and compute the success rate.

### 2. Prompt & Overlay Tuning (R1)
- Modify `prompts/overlays/qwen.md` to:
  - Enforce strict python syntax and formatting (proper markdown diff format, avoiding empty placeholders).
  - Inject structured reasoning instructions (step-by-step thinking templates optimized for Qwen3.6).
  - Encourage robust usage of available workspace tools (such as Grep, Read, and diagnostics).
- Ensure overlays are compact (<20 lines of directives is a general guideline, but let's keep it highly dense and focused).

### 3. Core Engine Self-Correction (R2)
- Implement `check_syntax` helper supporting Python (AST parsing), JSON (json.loads), JavaScript (basic verification via `node --check`), and shell scripts (`bash -n`).
- Hook file writing/editing tools (`Write`, `Edit`, `NotebookEdit`) in the agent execution loop (`agent.py`) to track modified files.
- In `agent.py`'s loop, if the assistant is about to conclude the turn (no tool calls generated):
  - Iterate through the modified files and run `check_syntax`.
  - If a syntax error is found, print a message, append a system/user reminder detailing the syntax error to the conversation history, decrement a self-correction counter (limit to 3 attempts), and `continue` the loop (nudge the model to fix its error).
  - If a test command run via `Bash` fails, also feed back the error and request self-correction before concluding.

### 4. Verification & Validation
- Run the `tests/bench_coding.py` script.
- Verify success rate is >= 80% (at least 4/5 tasks pass).
- Verify that code with syntax errors is auto-corrected.
- Verify no regressions exist in other features.
