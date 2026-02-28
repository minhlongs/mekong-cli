# Phase 01 — Fix CLI Install + Environment

**Context:** [plan.md](plan.md) | [audit-results.md](research/audit-results.md)

## Overview
- **Date:** 2026-02-23
- **Priority:** P0 (blocker cho tất cả phases khác)
- **Status:** pending
- **Effort:** 30m

## Key Insights
- `mekong` binary không accessible vì package chưa installed vào venv
- `pyproject.toml` định nghĩa `mekong = "src.main:app"` nhưng `uv` không tự install
- `.venv` hiện tại thiếu: `rich`, `pyyaml`, `requests`, `pytest`, `typer`, `fastapi`, `pydantic`
- `uv.lock` tồn tại — project dùng `uv` làm package manager chính

## Requirements
- `mekong --version` phải chạy được từ project root
- `mekong cook "hello world"` phải không báo lỗi "command not found"
- `uv run python -m pytest tests/` phải pass 388 tests

## Related Files
- `pyproject.toml` — scripts definition
- `.venv/` — virtual environment hiện tại
- `uv.lock` — lock file
- `requirements.txt` — fallback requirements

## Implementation Steps

1. Install đầy đủ dependencies qua uv:
   ```bash
   cd /Users/macbookprom1/mekong-cli
   uv pip install rich pyyaml requests typer fastapi pydantic pydantic-settings python-dotenv
   uv pip install pytest pytest-asyncio httpx
   ```

2. Install package editable (để `mekong` CLI accessible):
   ```bash
   uv pip install -e .
   ```

3. Verify CLI:
   ```bash
   uv run mekong --version
   uv run mekong cook "hello world"
   ```

4. Fix FastAPI deprecation warnings (gateway.py):
   - Thay `@gateway.on_event("startup"/"shutdown")` → lifespan context manager
   - File: `src/core/gateway.py:508`

## Todo
- [ ] `uv pip install -e .` — install package editable
- [ ] Verify `mekong --version` works
- [ ] Verify `mekong cook "hello world"` works
- [ ] Fix `on_event` deprecation warnings trong `gateway.py`
- [ ] Re-run pytest để confirm 388+ pass

## Success Criteria
- `mekong cook "hello world"` chạy không lỗi
- pytest: 388 passed, 0 errors, warnings giảm

## Risk Assessment
- Low: chỉ là install/config, không sửa logic
- `uv pip install -e .` có thể conflict nếu pyproject.toml chưa valid với uv

## Next Steps
→ Phase 02: Self-Healing Integration
