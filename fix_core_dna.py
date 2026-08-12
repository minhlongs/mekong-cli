"""Insert CoreDna gate into authorize_command."""
with open("src/core/command_authorizer.py") as f:
    lines = f.readlines()

# Find the line with "Step 2: Check local license"
for i, line in enumerate(lines):
    if "Step 2: Check local license" in line:
        # Insert CoreDna gate before this line
        indent = line[:len(line) - len(line.lstrip())]
        gate = [
            f"{indent}# Step 1.5: Core DNA gate — block unknown local commands before license check\n",
            f"{indent}if self._is_unknown_local_command(command):\n",
            f"{indent}    return AuthorizationResult(\n",
            f'{indent}        allowed=False,\n',
            f'{indent}        reason=AuthorizationReason.CORE_DNA_BLOCKED,\n',
            f'{indent}        message=f"\'{{command}}\' is not a recognized CoreDNA command",\n',
            f"{indent}        is_cached=False,\n",
            f"{indent}    )\n",
            "\n",
        ]
        lines = lines[:i] + gate + lines[i:]
        print(f"✓ Inserted CoreDna gate at line {i+1}")
        break
else:
    print("✗ Could not find 'Step 2: Check local license'")

with open("src/core/command_authorizer.py", "w") as f:
    f.writelines(lines)
