#!/usr/bin/env python3
"""Fix SSRF TOCTOU in executor.py by adding IP pinning and re-validation."""
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

# Find line numbers of key sections
validate_start = None
for i, line in enumerate(lines):
    if "def _validate_url(url: str) -> str | None:" in line:
        validate_start = i
        break

# Find the end of _validate_url (next def at same indent)
validate_end = None
for i in range(validate_start + 1, len(lines)):
    if lines[i].startswith("def ") and not lines[i].startswith("    "):
        validate_end = i
        break

print(f"_validate_url at lines {validate_start+1}-{validate_end}")
print("First few lines:")
for i in range(validate_start, min(validate_start+5, len(lines))):
    print(f"  {i+1}: {lines[i]}", end="")
