#!/usr/bin/env python3
path = "/Users/macbook/mekong-cli/src/cli/goal_commands.py"
with open(path, "rb") as f:
    data = f.read()

# Find byte offset of target using debug output
anchor = b' _print_json(payload)\n return\n style = "green"'
idx = data.find(anchor)
print(f"anchor at {idx}")
print(f"context: {data[idx-20:idx+80]!r}")

if idx == -1:
    # Show first 100 lines to understand file
    lines = data.split(b"\n")
    for i, line in enumerate(lines[:100]):
        print(f"  {i+1}: {line!r}")
    raise SystemExit(1)

# EXACT replacement based on debug output
old = b' _print_json(payload)\n return\n'
replacement = b' _print_json(payload)\n  if goal.status != GoalStatus.SATISFIED:\n   raise typer.Exit(code=1)\n return\n'

new_data = data.replace(old, replacement, 1)
count = (len(new_data) - len(data)) // (len(replacement) - len(old))
print(f"replacements: {count}")

with open(path, "wb") as f:
    f.write(new_data)
print("Done")
