# Implementation Plan — CheetahClaws Self-Correction Updates

This plan details the changes required to implement self-correction, syntax checking, and exit code tracking in the CheetahClaws agent runner.

## 1. Modify `tools/shell.py`
- Location: `tools/shell.py` around line 100 in the `_bash` tool implementation.
- Change: If `proc.returncode != 0`, append `\n[exit code: {proc.returncode}]` to the returned output.
- Verification: Call `_bash` with a command that exits with a non-zero code (e.g. `ls non_existent_file`) and assert that the exit code is appended.

## 2. Modify `agent.py`
- Location: `agent.py`
- Helper function `check_file_syntax(file_path: str) -> str | None` at the module level (before `run`).
  - Checks syntax for:
    - Python AST: `ast.parse`
    - JSON: `json.loads`
    - JavaScript / Node: if suffix is `.js` / `.mjs` / `.cjs`, run `node --check <file>` via subprocess, return stderr if `returncode != 0` (catch `FileNotFoundError`).
    - Shell scripts: if suffix is `.sh` / `.bash` / `.zsh`, run `bash -n <file>` via subprocess, return stderr/stdout if `returncode != 0`.
- In `run(...)` (at the top of the function), initialize tracking variables:
  - `modified_files = set()`
  - `self_correction_attempts = 3`
  - `last_failed_test = None`
- In `run(...)` inside the tool execution loop where results are processed (around line 487):
  - Track modified files: if permitted, and the tool name is "Write" or "Edit" (extract "file_path") or "NotebookEdit" (extract "notebook_path"), resolve the absolute path and add to `modified_files`.
  - Track failed test commands: if permitted, and tool name is "Bash", and the command contains words like 'test', 'pytest', 'npm t', 'tox':
    - If the output contains `[exit code:`, store it in `last_failed_test` as a dict: `{"command": cmd, "output": result}`.
    - Otherwise (passed), set `last_failed_test = None`.
- In `run(...)` at the end of the assistant's turn (around line 302, right after `if not assistant_turn.tool_calls:`):
  - Run syntax check: loop through `modified_files`, and call `check_file_syntax` on each. If any error is returned:
    - Decrement `self_correction_attempts`.
    - If `self_correction_attempts > 0`, append a user nudge message to `state.messages` detailing the syntax errors, warning the model, and reminding it to fix them. Yield a `TextChunk` notifying the user, and `continue` the loop.
  - Run failed test check: if `last_failed_test` is not None:
    - Decrement `self_correction_attempts`.
    - If `self_correction_attempts > 0`, append a user nudge message to `state.messages` detailing the failed test output and command. Yield a `TextChunk` notifying the user, and `continue` the loop.

## 3. Update `prompts/overlays/qwen.md`
- Location: `prompts/overlays/qwen.md`
- Change: Under Output Quality, add clear instructions enforcing strictly valid python/JSON/JS syntax, avoiding empty placeholders, and instructing the model on how to handle syntax self-correction nudges from the engine.

## 4. Verification & Testing
- Use python compiler syntax checks: `python3 -m py_compile agent.py tools/shell.py`.
- Run project test command to verify existing tests pass.
- Write/update tests to cover these features.
