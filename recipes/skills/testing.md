# Testing Skill — Best Practices

## Standards
- pytest as the test runner
- Fixtures in `conftest.py` for shared setup
- Test naming: `test_<unit>_<scenario>_<expected>`
- Aim for > 80% coverage on core modules

## Patterns
- AAA pattern: Arrange, Act, Assert
- Use `tmp_path` fixture for filesystem tests
- `monkeypatch` for environment and attribute mocking
- Parametrize for multiple input/output cases

## Gotchas
- Don't mock what you don't own — wrap external APIs
- Avoid test interdependence — each test must be isolated
- `conftest.py` fixtures are scoped: function/class/module/session
- Use `-x` flag to stop on first failure during development

## Commands
- `python3 -m pytest tests/ -x -q` — fast dev feedback
- `python3 -m pytest tests/ -v --tb=short` — verbose with short tracebacks
- `python3 -m pytest --cov=src tests/` — with coverage report
