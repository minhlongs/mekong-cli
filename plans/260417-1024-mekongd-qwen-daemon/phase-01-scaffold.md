# Phase 01 — Package Scaffold, CLI, Config, Stats Schema

## Context Links

- Plan: [plan.md](./plan.md)
- Research: [research-260417-1024-qwen36-solo-company.md](../reports/research-260417-1024-qwen36-solo-company.md)
- SQLite reference: `/Users/macbookprom1/mekong-cli/src/core/signals/local_store.py`
- Typer sub-app reference: `/Users/macbookprom1/mekong-cli/src/cli/sdlc/spec.py`

## Overview

- **Priority:** P1 (blocks all downstream phases)
- **Status:** pending
- **Description:** Create `packages/mekongd/` Python package with `pyproject.toml`, Typer CLI skeleton (`serve|stats|config`), pydantic-settings config loader, and SQLite stats DB schema initializer. No network/LLM code. This phase unblocks Phase 02 and 03.

## Key Insights

- Monorepo subfolder (decision deferred from research Q1) — keeps ship-in-week velocity, shares CI infra.
- Reuse SQLite pattern from `core/signals/local_store.py`: WAL mode, idempotent schema, swallow-exceptions write.
- Typer sub-app pattern matches existing `mekong sdlc` commands — consistent UX.
- Config via `pydantic-settings` env-first (matches solo-company doctrine: zero-config for user).

## Requirements

### Functional

- `mekongd --help` prints 3 commands: `serve`, `stats`, `config`.
- `mekongd serve` (stub) prints "serve not yet implemented" — exits 0.
- `mekongd stats` prints "0 tokens routed" on fresh DB.
- `mekongd config` dumps effective config (port, DB path, model path).
- `Settings` class loads from env: `MEKONGD_PORT`, `MEKONGD_DB_PATH`, `MEKONGD_MODEL_PATH`, `MEKONGD_CLOUD_API_KEY`.
- SQLite DB auto-creates on first stats read/write. Default path: `~/.mekongd/stats.sqlite`.

### Non-Functional

- Python 3.11+ only (MLX requires it).
- `mekongd` entry-point registered via `[project.scripts]` — installs as CLI.
- Zero runtime deps beyond: `typer`, `pydantic`, `pydantic-settings`.
- `pytest tests/test_config.py` + `test_stats.py` green.

## Architecture

```
+-----------------------------+
|  mekongd (Typer app)        |
|  cli.py                     |
+-----+-----------+-----------+
      |           |
      v           v
+-----------+  +-----------+
| config.py |  | stats.py  |
| Settings  |  | init_db() |
| load_cfg()|  | row_count |
+-----------+  +-----+-----+
                     |
                     v
            ~/.mekongd/stats.sqlite
            (missions table schema,
             WAL mode)
```

Data flow: CLI command → resolves `Settings` from env → invokes subcommand → reads/writes SQLite.

## Related Code Files

### To Create

- `/Users/macbookprom1/mekong-cli/packages/mekongd/pyproject.toml`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/README.md`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/__init__.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/cli.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/config.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/stats.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/tests/__init__.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/tests/test_config.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/tests/test_stats.py`

### To Modify

- None (new package, isolated subdir).

## Implementation Steps

1. Create `packages/mekongd/pyproject.toml` with `[project]` PEP-621 metadata: name=`mekongd`, python>=3.11, deps=`typer,pydantic,pydantic-settings`, dev-deps=`pytest,pytest-asyncio`, extras `mlx=[mlx,mlx-lm]` and `proxy=[fastapi,uvicorn,sse-starlette,httpx]`.
2. Register entry-point: `[project.scripts] mekongd = "mekongd.cli:app"`.
3. Write `mekongd/config.py`:
   ```python
   class Settings(BaseSettings):
       port: int = 8765
       host: str = "127.0.0.1"
       db_path: Path = Path.home() / ".mekongd" / "stats.sqlite"
       model_path: Path = Path.home() / ".mekongd" / "models" / "qwen3.6-35b-a3b-mlx-q4"
       cloud_api_key: str | None = None
       cloud_base_url: str = "https://api.anthropic.com"
       model_config = SettingsConfigDict(env_prefix="MEKONGD_", env_file=".env")
   def load_settings() -> Settings: ...
   ```
4. Write `mekongd/stats.py` schema + init (mirrors `local_store.py`):
   ```python
   _SCHEMA_SQL = """
   CREATE TABLE IF NOT EXISTS routing_events (
       id            INTEGER PRIMARY KEY AUTOINCREMENT,
       ts            TEXT    NOT NULL,
       route         TEXT    NOT NULL,  -- 'local' | 'cloud'
       model         TEXT    NOT NULL,
       input_tokens  INTEGER NOT NULL DEFAULT 0,
       output_tokens INTEGER NOT NULL DEFAULT 0,
       latency_ms    INTEGER NOT NULL DEFAULT 0,
       est_cost_usd  REAL    NOT NULL DEFAULT 0.0
   );
   CREATE INDEX IF NOT EXISTS idx_routing_ts ON routing_events (ts);
   CREATE INDEX IF NOT EXISTS idx_routing_route ON routing_events (route);
   """
   def init_db(path: Path) -> sqlite3.Connection: ...
   def summarize(path: Path) -> dict: ...  # counts + total saved
   ```
5. Write `mekongd/cli.py` Typer app:
   ```python
   app = typer.Typer(name="mekongd", help="Local Qwen3.6 daemon for CC CLI cost savings.")
   @app.command() def serve(host: str = ..., port: int = ...): ...  # stub
   @app.command() def stats(): ...  # prints summarize() result
   @app.command() def config(): ...  # prints Settings
   ```
6. Write `tests/test_config.py`: verify env-override (monkeypatch `MEKONGD_PORT=9999`).
7. Write `tests/test_stats.py`: init empty DB, assert `summarize()` returns zero counts; write fake row, assert summary updates.
8. Write minimal `README.md` — install (`pip install -e .`), usage (3 commands), roadmap (phases 02/03).
9. Verify: `cd tools/mekongd && pip install -e . && mekongd --help && pytest`.

## Todo List

- [ ] Create `packages/mekongd/` directory tree
- [ ] Write `pyproject.toml` with PEP-621 + entry-point
- [ ] Write `mekongd/__init__.py` with `__version__ = "0.1.0"`
- [ ] Implement `config.py` with `Settings` + `load_settings()`
- [ ] Implement `stats.py` with schema + `init_db()` + `summarize()`
- [ ] Implement `cli.py` with 3 Typer commands (stubs where applicable)
- [ ] Write `tests/test_config.py` (env-override)
- [ ] Write `tests/test_stats.py` (init + summary)
- [ ] Write `README.md`
- [ ] Local verify: `pip install -e . && mekongd --help && pytest`

## Success Criteria

- `pip install -e tools/mekongd` succeeds.
- `mekongd --help` shows `serve`, `stats`, `config`.
- `mekongd stats` prints "routed: 0 local / 0 cloud / $0.00 saved" on fresh DB.
- `mekongd config` prints JSON-like dump of Settings.
- `pytest packages/mekongd/tests/` → 2 files, all green.
- No imports from `mlx`, `fastapi`, or `anthropic` (lazy deferred to Phase 02).

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| `pydantic-settings` v2 API drift | Pin `pydantic-settings>=2.1,<3` |
| Typer 0.12 vs 0.15 command registration differences | Pin `typer>=0.12,<0.16` matches main repo |
| DB default path in `$HOME` may be read-only in CI | Tests use `tmp_path` fixture, never `~` |

## Security Considerations

- Config secrets (`MEKONGD_CLOUD_API_KEY`) loaded from env only — never logged.
- DB path under `$HOME/.mekongd/` (user-scoped 0700).
- No network code in this phase — attack surface limited to file I/O.

## Next Steps

- Phase 02 depends on `Settings` + `init_db()` signatures frozen here.
- Phase 02 will add `[proxy]` extras usage (`fastapi`, `sse-starlette`, `httpx`) behind import guards so Phase 01 install stays minimal.

## Unresolved Questions

1. Should `MEKONGD_MODEL_PATH` default point to a Hugging Face repo-id instead of local dir? (defer — user must download explicitly in v0)
2. Multi-user DB isolation (per-repo `.mekongd.sqlite`) — needed for v0 or defer? (defer; user-home scope fine for MVP)
