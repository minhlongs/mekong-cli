# Python Skill — Best Practices

## Standards
- Type hints on ALL functions (PEP 484)
- Docstrings on all public classes and methods (Google style)
- snake_case for functions/variables, PascalCase for classes
- File size < 200 lines — split into modules

## Patterns
- Use `pathlib.Path` over `os.path`
- Prefer `dataclasses` or `pydantic` for data structures
- Use `from __future__ import annotations` for forward refs
- Context managers for resource management

## Gotchas
- Mutable default arguments: use `field(default_factory=list)`
- Import cycles: use `TYPE_CHECKING` guard
- Always specify `encoding="utf-8"` for file I/O
- `subprocess.run` needs `timeout` parameter

## Testing
- pytest with `-x -q` for fast feedback
- Fixtures in `conftest.py`
- Mock external calls, never hit real APIs in tests
