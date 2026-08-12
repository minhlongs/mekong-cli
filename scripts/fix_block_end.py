#!/usr/bin/env python3
"""Fix BLOCK_END in apply_trial_patch_v11.py: 1 space -> 4 spaces before 'return {'"""

# Read file
with open('scripts/apply_trial_patch_v11.py', 'r') as f:
    lines = f.readlines()

# Find ONLY the actual assignment line (line 37, uses double quotes)
for i, line in enumerate(lines):
    # Target specifically: starts with BLOCK_END = and uses double-quoted string
    if line.strip().startswith('BLOCK_END = "') and 'return {' in line:
        print(f"Found line {i+1}: {repr(line)}")
        # The string literal contains the escape sequences: )\n\n\n return {
        # We need to change the single space before 'return' to 4 spaces
        old_str = ')\n\n\n return {'
        new_str = ')\n\n\n    return {'
        if old_str in line:
            lines[i] = line.replace(old_str, new_str, 1)
            print(f"Fixed line {i+1}: {repr(lines[i][:90])}")
        else:
            print(f"Pattern '{old_str}' not found in line")
            # Extract the inner string to debug
            dq_start = line.index('"')
            dq_end = line.rindex('"')
            inner = line[dq_start+1:dq_end]
            print(f"Inner string: {repr(inner)}")
        break
else:
    print("ERROR: No matching line found")

with open('scripts/apply_trial_patch_v11.py', 'w') as f:
    f.writelines(lines)
print("\nVerifying...")

# Verify the fix
with open('scripts/apply_trial_patch_v11.py', 'r') as f:
    vlines = f.readlines()
for i, line in enumerate(vlines):
    if line.strip().startswith('BLOCK_END = "'):
        dq_start = line.index('"')
        dq_end = line.rindex('"')
        inner = line[dq_start+1:dq_end]
        # Find the last \n escape sequence
        last_nl_pos = inner.rfind('\\n')
        if last_nl_pos >= 0:
            after = inner[last_nl_pos+2:]
            spaces = len(after) - len(after.lstrip(' '))
            print(f"Line {i+1}: {spaces} spaces after last \\n escape")
            print(f"  Full inner: {repr(inner)}")
            # Also execute it to confirm
            exec(f"TEST_VAR = {repr(line.split('=')[1].split('#')[0].strip())}")
            print(f"  Evaluated value: {repr(TEST_VAR)}")
            eval_spaces = len(TEST_VAR) - len(TEST_VAR.rstrip('\n').rstrip(' '))
            last_eval_nl = TEST_VAR.rfind('\n')
            if last_eval_nl >= 0:
                eval_after = TEST_VAR[last_eval_nl+1:]
                print(f"  Evaluated spaces after newline: {len(eval_after) - len(eval_after.lstrip(' '))}")
                print(f"  Evaluated after newline: {repr(eval_after[:15])}")
