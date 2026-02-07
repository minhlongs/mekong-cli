import json
import os
from typing import Any, Dict, List, Optional, Union

class MockPostgrestBuilder:
    def __init__(self, table_name: str, db: "MockClient"):
        self.table_name = table_name
        self.db = db
        self._query = {}
        self._filters = []
        self._action = None
        self._data = None
        self._on_conflict = None

    def select(self, columns: str = "*") -> "MockPostgrestBuilder":
        self._action = "select"
        self._query["columns"] = columns
        return self

    def insert(self, data: Union[Dict, List[Dict]]) -> "MockPostgrestBuilder":
        self._action = "insert"
        self._data = data
        return self

    def update(self, data: Dict) -> "MockPostgrestBuilder":
        self._action = "update"
        self._data = data
        return self

    def upsert(self, data: Union[Dict, List[Dict]], on_conflict: str = None) -> "MockPostgrestBuilder":
        self._action = "upsert"
        self._data = data
        self._on_conflict = on_conflict
        return self

    def eq(self, column: str, value: Any) -> "MockPostgrestBuilder":
        self._filters.append(("eq", column, value))
        return self

    def execute(self) -> Any:
        return self.db._execute(self)

class MockResponse:
    def __init__(self, data: Any):
        self.data = data

class MockClient:
    def __init__(self, storage_file: str = "local_db.json"):
        self.storage_file = storage_file
        self._load()

    def _load(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    self.store = json.load(f)
            except:
                self.store = {}
        else:
            self.store = {}

    def _save(self):
        with open(self.storage_file, "w") as f:
            json.dump(self.store, f, indent=2)

    def table(self, name: str) -> MockPostgrestBuilder:
        return MockPostgrestBuilder(name, self)

    def from_(self, name: str) -> MockPostgrestBuilder:
        return self.table(name)

    def _execute(self, builder: MockPostgrestBuilder) -> MockResponse:
        self._load() # Reload to get latest state
        table = self.store.setdefault(builder.table_name, [])

        if builder._action == "select":
            results = table
            for op, col, val in builder._filters:
                if op == "eq":
                    results = [r for r in results if r.get(col) == val]
            return MockResponse(results)

        elif builder._action == "insert":
            new_rows = builder._data if isinstance(builder._data, list) else [builder._data]
            table.extend(new_rows)
            self._save()
            return MockResponse(new_rows)

        elif builder._action == "update":
            updated = []
            for row in table:
                match = True
                for op, col, val in builder._filters:
                    if op == "eq" and row.get(col) != val:
                        match = False
                        break
                if match:
                    row.update(builder._data)
                    updated.append(row)
            self._save()
            return MockResponse(updated)

        elif builder._action == "upsert":
            # Simple upsert logic
            upsert_data = builder._data if isinstance(builder._data, list) else [builder._data]

            # Key to check conflict on (defaulting to 'id' or first key if not specified, usually passed in builder)
            conflict_key = builder._on_conflict or "id"

            for new_row in upsert_data:
                # Find existing
                existing_idx = -1
                for i, row in enumerate(table):
                    # Check if conflict key matches (simplification: assume conflict key exists in data)
                    if conflict_key in row and conflict_key in new_row:
                         if row[conflict_key] == new_row[conflict_key]:
                             existing_idx = i
                             break
                    # Fallback for licenses table which uses license_key
                    if "license_key" in row and "license_key" in new_row:
                         if row["license_key"] == new_row["license_key"]:
                             existing_idx = i
                             break

                if existing_idx >= 0:
                    table[existing_idx].update(new_row)
                else:
                    table.append(new_row)

            self._save()
            return MockResponse(upsert_data)

        return MockResponse([])
