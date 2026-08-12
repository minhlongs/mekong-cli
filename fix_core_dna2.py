"""Fix _is_unknown_local_command — block ALL local commands unless contribution evidence."""

with open("src/core/command_authorizer.py") as f:
    lines = f.readlines()

# Find and replace the _is_unknown_local_command method
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "def _is_unknown_local_command(self, command: str) -> bool:" in line:
        start_idx = i
    if start_idx is not None and end_idx is None:
        # Find the next method definition at the same indentation level
        if i > start_idx and line.strip().startswith("def ") and not line.strip().startswith("def _is_unknown"):
            end_idx = i
            break

if start_idx is None or end_idx is None:
    print(f"✗ Could not find method bounds: start={start_idx}, end={end_idx}")
else:
    new_method = '''    def _is_unknown_local_command(self, command: str) -> bool:
        """Return True if command should be blocked by Core DNA gate.

        Blocks any command with a local-only prefix (private-, local-, core-)
        unless MEKONG_CONTRIBUTION_PR env var is set (contribution evidence).
        """
        import os
        local_prefixes = ("private-", "local-", "core-")
        if not command.startswith(local_prefixes):
            return False
        # Allow if contribution evidence provided
        if os.environ.get("MEKONG_CONTRIBUTION_PR"):
            return False
        return True

'''
    lines = lines[:start_idx] + [new_method] + lines[end_idx:]
    with open("src/core/command_authorizer.py", "w") as f:
        f.writelines(lines)
    print(f"✓ Fixed _is_unknown_local_command (lines {start_idx+1}-{end_idx})")
