#!/usr/bin/env python3
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()
for i in range(119, 165):
    print(f"{i+1}: {lines[i]}", end="")
