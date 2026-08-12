import re

# Fix 1: pev_adapter.py - reorder fallback_store init before try
with open('/Users/macbook/mekong-cli/src/core/adapters/pev_adapter.py', 'r') as f:
    content = f.read()

# Extract the __init__ block
old_init = '''    def __init__(self) -> None:
        try:
            from src.harness.pev.memory import MemoryStore as PevMemoryStore
            self._store = PevMemoryStore()
            self._has_pev = True
        except Exception:
            self._has_pev = False
            self._store = None # type: ignore[assignment]
            self._fallback_store: dict[str, Any] = {}'''

new_init = '''    def __init__(self) -> None:
        self._fallback_store: dict[str, Any] = {}
        try:
            from src.harness.pev.memory import MemoryStore as PevMemoryStore
            self._store = PevMemoryStore()
            self._has_pev = True
        except Exception:
            self._has_pev = False
            self._store = None # type: ignore[assignment]'''

assert old_init in content, "pev_adapter __init__ block not found"
content = content.replace(old_init, new_init)

# Fix 2: _data -> _store everywhere in pev_adapter
content = content.replace('self._store._data', 'self._store._store')

with open('/Users/macbook/mekong-cli/src/core/adapters/pev_adapter.py', 'w') as f:
    f.write(content)
print("Fixed pev_adapter.py")

# Fix 3: scoped_adapter.py - use broad scope for unfiltered search
with open('/Users/macbook/mekong-cli/src/core/adapters/scoped_adapter.py', 'r') as f:
    content = f.read()

old_search = '''    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        kind: MemoryKind | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> list[MemoryRecord]:
        """Search by query string, filtering client-side."""
        from src.core.memory_scope import MemoryScope # noqa: F401
        scope = self._make_scope(
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
        )'''

new_search = '''    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        kind: MemoryKind | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> list[MemoryRecord]:
        """Search by query string, filtering client-side."""
        from src.core.memory_scope import MemoryScope # noqa: F401
        scope = self._make_scope(
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
        )
        # When no scope filters are provided, query all stored entries
        # so client-side filtering still has something to work with.
        if agent_id is None and session_id is None and user_id is None:
            scope = MemoryScope()'''

assert old_search in content, "scoped_adapter search block not found"
content = content.replace(old_search, new_search)

with open('/Users/macbook/mekong-cli/src/core/adapters/scoped_adapter.py', 'w') as f:
    f.write(content)
print("Fixed scoped_adapter.py")
