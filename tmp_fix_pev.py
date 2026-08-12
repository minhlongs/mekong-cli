#!/usr/bin/env python3
"""Fix the crash_signals test in test_pev_self_healing.py"""
import re

path = "tests/test_pev_self_healing.py"
with open(path, "r") as f:
    content = f.read()

# Fix 1: Replace _execute_shell_step with execute_step in the crash_signals test
# The key is line 378: result = executor._execute_shell_step(step)
# We need to replace this and the surrounding with patch(...) block
old_block = """      with patch("src.harness.pev.executor.subprocess.run", return_value=proc):
         result = executor._execute_shell_step(step)"""

new_block = """      with patch.object(executor, "execute_step", wraps=executor.execute_step):
         result = executor.execute_step(step)"""

if old_block in content:
    content = content.replace(old_block, new_block)
    print(f"Fixed: replaced _execute_shell_step with execute_step")
else:
    print("ERROR: Old block not found")
    print("Searching for _execute_shell_step near line 378...")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '_execute_shell_step' in line and i > 370 and i < 390:
            print(f"Line {i+1}: {repr(line)}")

with open(path, "w") as f:
    f.write(content)
print(f"Done! Wrote to {path}")
