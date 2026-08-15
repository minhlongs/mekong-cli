#!/usr/bin/env python3
"""Fix SSRF TOCTOU bug - initialize pinned_ip before try block."""

path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

# Find line "        try:" after "# Try parsing as literal IP first, capture for pinning"
# and insert "pinned_ip = None" before it
for i, line in enumerate(lines):
    if "# Try parsing as literal IP first, capture for pinning" in line:
        # Next line is "        try:", insert before it
        indent = "        "
        lines.insert(i + 1, indent + "pinned_ip = None\n")
        print(f"Inserted pinned_ip = None at line {i+2}")
        break

with open(path, "w") as f:
    f.writelines(lines)
print("Done")
