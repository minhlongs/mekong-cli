#!/usr/bin/env python3
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()
for i in range(115, 125):
    print(f"Line {i+1}: leading={len(lines[i])-len(lines[i].lstrip())} | {repr(lines[i][:80])}")
