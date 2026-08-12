"""Fix command_authorizer.py — add CoreDna gate + fix memory_scope query."""

# ===== Fix 1: command_authorizer.py — add CoreDna gate =====
with open("src/core/command_authorizer.py") as f:
    src = f.read()

# Add the is_unknown_local_command check between free command and license check
old = """    # Step 1: FREE commands don't need authorization
    if self.is_free_command(command):
        return AuthorizationResult(
            allowed=True,
            reason=AuthorizationReason.FREE_COMMAND,
            message=f"'{command}' is a free command",
        )

    # Step 2: Check local license"""

new = """    # Step 1: FREE commands don't need authorization
    if self.is_free_command(command):
        return AuthorizationResult(
            allowed=True,
            reason=AuthorizationReason.FREE_COMMAND,
            message=f"'{command}' is a free command",
        )

    # Step 1.5: Core DNA gate — block unknown local commands before license check
    if self._is_unknown_local_command(command):
        return AuthorizationResult(
            allowed=False,
            reason=AuthorizationReason.CORE_DNA_BLOCKED,
            message=f"'{command}' is not a recognized CoreDNA command",
            is_cached=False,
        )

    # Step 2: Check local license"""

if old in src:
    src = src.replace(old, new)
    print("✓ Added CoreDna gate check in authorize_command")
else:
    print("✗ Could not find insertion point for CoreDna gate")

# Add the _is_unknown_local_command method to CommandAuthorizer class
method = '''
    def _is_unknown_local_command(self, command: str) -> bool:
        """Return True if command is unknown AND has local-only markers.

        A command is treated as local-only if its name starts with
        'private-', 'local-', or 'core-' — these are not intended for
        public API exposure. Unknown commands without those markers
        (e.g. 'community-feature') are handled by the tier-gate
        fallback instead.
        """
        local_prefixes = ("private-", "local-", "core-")
        if not command.startswith(local_prefixes):
            return False
        # Known local commands that are explicitly allowed
        known_local = {
            "private-local-updater",
        }
        return command not in known_local
'''

# Insert before the authorize_command method (line 492 = first "def authorize_command")
insert_marker = "    def authorize_command(self, command: str) -> AuthorizationResult:"
if insert_marker in src and "_is_unknown_local_command" not in src:
    src = src.replace(insert_marker, method + "\n" + insert_marker, 1)
    print("✓ Added _is_unknown_local_command method")
else:
    if "_is_unknown_local_command" in src:
        print("! Method already exists, skipping")
    else:
        print("✗ Could not find authorize_command method")

with open("src/core/command_authorizer.py", "w") as f:
    f.write(src)

# ===== Fix 2: memory_scope.py — fix query() access control =====
with open("src/core/memory_scope.py") as f:
    scope_src = f.read()

old_query = """    def query(self, scope: MemoryScope) -> list[ScopedMemoryEntry]:
        \"\"\"Return all non-expired entries accessible to *scope*.

        Includes entries where agent_id is None (shared) as well as entries
        owned by the same agent.
        \"\"\"
        results: list[ScopedMemoryEntry] = []
        for entry in list(self._store.values()):
            if entry.is_expired():
                continue
            results.append(entry)
        return results"""

new_query = """    def query(self, scope: MemoryScope) -> list[ScopedMemoryEntry]:
        \"\"\"Return non-expired entries accessible to *scope*.

        Enforces access-control: only returns entries the requesting
        scope is allowed to read (same app + org + user; agent match
        or agent_id=None for shared entries).
        \"\"\"
        results: list[ScopedMemoryEntry] = []
        for entry in list(self._store.values()):
            if entry.is_expired():
                continue
            if validate_access(scope, entry.scope):
                results.append(entry)
        return results"""

if old_query in scope_src:
    scope_src = scope_src.replace(old_query, new_query)
    print("✓ Fixed query() to enforce access control")
else:
    print("✗ Could not find query() method to fix")

with open("src/core/memory_scope.py", "w") as f:
    f.write(scope_src)

print("\nDone — run tests to verify")
