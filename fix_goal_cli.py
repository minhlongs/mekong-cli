#!/usr/bin/env python3
"""Fix goal_run and goal_verify json_output blocks."""
from pathlib import Path

path = Path("/Users/macbook/mekong-cli/src/cli/goal_commands.py")
lines = path.read_text().split("\n")

# --- Collect changes first, apply cleanly after ---
inserts: list[tuple[int, list[str]]] = []  # (line_index_0based, lines_to_insert_after)

current = ""
for i, raw in enumerate(lines):
    s = raw.strip()
    if s.startswith("def goal_"):
        current = s.split("(")[0].replace("def ", "")
        continue

    # Only act once per function
    if current == "goal_run" and s == "_print_json(payload)":
        # Next line is  return
        if i + 1 < len(lines) and lines[i + 1].strip() == "return":
            inserts.append((i, [
                "  if goal.status != GoalStatus.SATISFIED:",
                "   raise typer.Exit(code=1)",
            ]))
        current = ""
        continue

    if current == "goal_verify" and s == "_print_json(payload)":
        # Find where the if json_output block ends
        j = i + 1
        while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith("def "):
            j += 1
        # Insert return at end of block (before the blank line or next def)
        inserts.append((j - 1, ["  return"]))
        current = ""
        continue

# Apply inserts in reverse order so line numbers stay valid
for idx, new_lines in sorted(inserts, reverse=True):
    lines[idx + 1:idx + 1] = new_lines

path.write_text("\n".join(lines))
print(f"Done. Applied {len(inserts)} inserts.")
