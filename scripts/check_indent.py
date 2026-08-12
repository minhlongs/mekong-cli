#!/usr/bin/env python3
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

# Check line 120 whitespace
line = lines[119]
print(f"Line 120 repr: {repr(line)}")
print(f"Leading spaces: {len(line) - len(line.lstrip())}")

# Check lines 140-145
for i in range(139, 150):
    print(f"Line {i+1}: leading={len(lines[i])-len(lines[i].lstrip())} | {repr(lines[i][:60])}")
