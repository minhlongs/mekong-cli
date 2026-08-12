#!/usr/bin/env python3
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()
# Remove stray @staticmethod at line 119 (index 118)
del lines[118]
with open(path, "w") as f:
    f.writelines(lines)
print("Removed stray @staticmethod")
