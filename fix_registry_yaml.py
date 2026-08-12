#!/usr/bin/env python3
"""Fix under-indented lines in agents/registry.yaml."""
import yaml
import sys

path = "agents/registry.yaml"
with open(path) as f:
    lines = f.readlines()

fixed = []
changes = 0
for line in lines:
    stripped = line.rstrip('\n')
    if not stripped:
        fixed.append(line)
        continue
    if stripped.startswith('#'):
        fixed.append(line)
        continue
    leading = len(stripped) - len(stripped.lstrip())
    if 0 < leading < 4 and not stripped.lstrip().startswith('#'):
        new_line = '  ' + stripped + '\n'
        if new_line != line:
            changes += 1
            print(f" Fix: {repr(line.rstrip())} -> {repr(new_line.rstrip())}")
        fixed.append(new_line)
        continue
    fixed.append(line)

if changes == 0:
    print("No changes needed")
    sys.exit(0)

with open(path, "w") as f:
    f.writelines(fixed)

print(f"\nFixed {changes} lines")
with open(path) as f:
    data = yaml.safe_load(f)
agents = data.get('agents', [])
print(f"Parse OK -- {len(agents)} agents loaded")
for a in agents:
    print(f" {a.get('id')}: {a.get('name')}")
