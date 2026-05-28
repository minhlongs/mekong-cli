## 2026-05-27T15:03:03Z
Please implement the self-correction engine updates in CheetahClaws codebase under /Users/macbook/.local/share/uv/tools/cheetahclaws/lib/python3.14/site-packages.

Here are the specific tasks:

1. Update `tools/shell.py` (around line 100) inside the `_bash` tool implementation:
If `proc.returncode != 0`, append `\n[exit code: {proc.returncode}]` to the return output. This enables the agent runner to track failed commands programmatically.

2. Update `agent.py` to support syntax checking and self-correction:
- Implement a helper function `check_file_syntax(file_path: str) -> str | None` at the module level (before `run`). It should check syntax using:
  - Python AST: `ast.parse`
  - JSON: `json.loads`
  - JavaScript / Node: if suffix is .js/.mjs/.cjs, execute `node --check <file>` via subprocess and return stderr if returncode != 0 (catch FileNotFoundError gracefully if node is not installed).
  - Shell scripts: if suffix is .sh/.bash/.zsh, execute `bash -n <file>` via subprocess and return stderr/stdout if returncode != 0.
- In `run(...)` (at the top of the function), initialize tracking variables:
  - `modified_files = set()`
  - `self_correction_attempts = 3
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

3. Update `prompts/overlays/qwen.md`:
- Under Output Quality, add clear instructions enforcing strictly valid python/JSON/JS syntax, avoiding empty placeholders, and instructing the model on how to handle syntax self-correction nudges from the engine.

Verify all code changes. Do NOT cheat. Do NOT hardcode results. Make sure to run syntax validation (like `python3 -m py_compile agent.py` or similar checks) on your edits to ensure they compile correctly. Write a handoff report in your folder once done.
