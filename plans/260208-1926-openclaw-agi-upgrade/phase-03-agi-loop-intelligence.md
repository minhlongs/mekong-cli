# Phase 3: AGI Loop Intelligence

## Context Links

- Source: `/Users/macbookprom1/mekong-cli/src/core/agi_loop.py` (430 lines)
- Research: [AGI Loop Hardening](research/researcher-02-agi-loop-memory-decay.md)
- Depends on: Phase 1 (LLM client resilience)

## Overview

- **Priority**: P1
- **Status**: pending
- **Effort**: 1.5h

Persist improvement history, add self-testing after CC CLI execution, git rollback on test failure, adaptive cooldown, and deduplication.

## Key Insights

- `completed_improvements` is in-memory list of IDs -- lost on restart (line 94)
- `_execute()` only checks CC CLI exit code, never runs tests (lines 236-279)
- Fixed 90s cooldown regardless of success/failure pattern (line 81)
- No dedup -- Gemini may suggest same improvement repeatedly after restart
- Test suite takes ~2.5min -- use `pytest -x -q` (fast-fail, quiet) for AGI self-test

## Requirements

- Persist history to `~/.mekong/agi_history.json` (load on init, save after each cycle)
- After CC CLI success, run `python3 -m pytest tests/ -x -q`
- On test failure: `git checkout -- .` to rollback, mark improvement as FAILED
- Adaptive cooldown: speed up on success streak, slow down on failure
- Blacklist: skip improvements that failed 2+ times within 24h
- `get_status()` method exposing metrics for Telegram (Phase 5)

## Architecture

```
~/.mekong/agi_history.json:
{
  "completed": ["id1", "id2", ...],
  "blacklist": {"id3": {"count": 2, "last": 1707400000}},
  "details": [{"id": "id1", "title": "...", "category": "...", "timestamp": 1707400000, "success": true}]
}
```

## Related Code Files

- **Modify**: `src/core/agi_loop.py`

## Implementation Steps

1. Add imports at top (after line 24):
   ```python
   from pathlib import Path
   ```

2. Add history path constant (after line 27):
   ```python
   HISTORY_PATH = Path.home() / ".mekong" / "agi_history.json"
   ```

3. Add `_load_history()` and `_save_history()` methods to `AGILoop`:
   ```python
   def _load_history(self) -> dict:
       if HISTORY_PATH.exists():
           try:
               return json.loads(HISTORY_PATH.read_text())
           except (json.JSONDecodeError, OSError):
               return {"completed": [], "blacklist": {}, "details": []}
       return {"completed": [], "blacklist": {}, "details": []}

   def _save_history(self):
       HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
       # Keep last 100 entries
       self._history["completed"] = self._history["completed"][-100:]
       self._history["details"] = self._history["details"][-100:]
       HISTORY_PATH.write_text(json.dumps(self._history, indent=2))
   ```

4. In `__init__` (after line 96), load history:
   ```python
   self._history = self._load_history()
   self.completed_improvements = self._history.get("completed", [])
   self.start_time = time.time()
   self.last_success_time: Optional[float] = None
   ```

5. Add `_is_blacklisted()` method:
   ```python
   def _is_blacklisted(self, improvement_id: str) -> bool:
       bl = self._history.get("blacklist", {}).get(improvement_id, {})
       if bl.get("count", 0) >= 2:
           return (time.time() - bl.get("last", 0)) < 86400
       return False
   ```

6. In `run_forever()`, after `_assess()` returns (line 131-135), add blacklist check:
   ```python
   improvement = await self._assess()
   if not improvement:
       ...
       continue
   imp_id = improvement.get("improvement_id", "")
   if self._is_blacklisted(imp_id):
       logger.info(f"Skipping blacklisted improvement: {imp_id}")
       continue
   ```

7. Add `_verify_tests()` async method:
   ```python
   async def _verify_tests(self) -> tuple:
       proc = await asyncio.create_subprocess_exec(
           "python3", "-m", "pytest", "tests/", "-x", "-q",
           stdout=asyncio.subprocess.PIPE,
           stderr=asyncio.subprocess.PIPE,
           cwd=str(Path(__file__).resolve().parent.parent.parent),
       )
       stdout, stderr = await proc.communicate()
       passed = proc.returncode == 0
       output = (stdout or b"").decode()[-500:]
       return passed, output
   ```

8. Add `_git_rollback()` async method:
   ```python
   async def _git_rollback(self):
       proc = await asyncio.create_subprocess_exec(
           "git", "checkout", "--", ".",
           cwd=str(Path(__file__).resolve().parent.parent.parent),
       )
       await proc.communicate()
       logger.info("Git rollback completed")
   ```

9. Modify `_execute()`: after CC CLI succeeds (line 270), add test verification:
   ```python
   if session.status.value == "completed":
       logger.info("CC CLI completed. Running tests...")
       tests_passed, test_output = await self._verify_tests()
       if not tests_passed:
           logger.warning(f"Tests failed after improvement. Rolling back.\n{test_output}")
           await self._git_rollback()
           return False
       logger.info("Tests passed!")
       return True
   ```

10. After success/failure tracking (lines 146-152), persist history:
    ```python
    if success:
        self.consecutive_failures = 0
        self.completed_improvements.append(imp_id)
        self.last_success_time = time.time()
        self._history["completed"] = self.completed_improvements
        self._history["details"].append({
            "id": imp_id, "title": improvement.get("title", ""),
            "category": improvement.get("category", ""),
            "timestamp": time.time(), "success": True,
        })
    else:
        self.consecutive_failures += 1
        bl = self._history.setdefault("blacklist", {})
        entry = bl.setdefault(imp_id, {"count": 0, "last": 0})
        entry["count"] += 1
        entry["last"] = time.time()
    self._save_history()
    ```

11. Add `_calculate_cooldown()` method:
    ```python
    def _calculate_cooldown(self) -> int:
        if self.consecutive_failures == 0:
            streak = len([d for d in self._history.get("details", [])[-5:]
                         if d.get("success")])
            if streak >= 3:
                return max(30, self.cooldown // 2)
            return self.cooldown
        return min(self.cooldown * (2 ** self.consecutive_failures), 600)
    ```

12. Replace fixed cooldown in `run_forever()` (line 161-162):
    ```python
    actual_cooldown = self._calculate_cooldown()
    logger.info(f"Cooling down {actual_cooldown}s...")
    await self._safe_sleep(actual_cooldown)
    ```

13. Add `get_status()` method for Phase 5:
    ```python
    def get_status(self) -> dict:
        uptime = time.time() - self.start_time if self.start_time else 0
        total = len(self._history.get("details", []))
        successes = len([d for d in self._history.get("details", []) if d.get("success")])
        rate = (successes / total * 100) if total > 0 else 0
        last = self._history.get("details", [])[-1] if self._history.get("details") else None
        return {
            "running": self._running,
            "iteration": self.iteration,
            "improvements": len(self.completed_improvements),
            "consecutive_failures": self.consecutive_failures,
            "success_rate": round(rate, 1),
            "uptime_seconds": int(uptime),
            "last_improvement": last,
            "cooldown": self._calculate_cooldown(),
        }
    ```

## Todo List

- [ ] Add HISTORY_PATH constant
- [ ] Add `_load_history()` / `_save_history()`
- [ ] Load history in `__init__`, add `start_time`, `last_success_time`
- [ ] Add `_is_blacklisted()`
- [ ] Add blacklist check after `_assess()`
- [ ] Add `_verify_tests()` -- run pytest after CC CLI
- [ ] Add `_git_rollback()` -- git checkout on test failure
- [ ] Integrate test verification into `_execute()`
- [ ] Persist history after each success/failure
- [ ] Add `_calculate_cooldown()` -- adaptive cooldown
- [ ] Replace fixed cooldown with adaptive
- [ ] Add `get_status()` for Telegram
- [ ] Run `python3 -m pytest tests/ -v` -- all tests pass

## Success Criteria

- `~/.mekong/agi_history.json` created and populated after first cycle
- History survives process restart
- Failed improvements blacklisted for 24h after 2 failures
- Tests run after each CC CLI execution; git rollback on failure
- Cooldown adapts: faster on success streak, slower on failure

## Risk Assessment

- **`git checkout -- .` safety**: Could discard user's uncommitted changes. Mitigated: AGI loop should only run on clean working tree. Add guard: check `git diff --stat` before execution
- **Test suite duration**: ~2.5min per cycle adds overhead. Use `-x` (stop on first failure) to minimize
- **History file corruption**: JSON write not atomic. Risk: low (single writer). Could use tempfile+rename if needed

## Security Considerations

- History file stored in user home dir (~/.mekong/) -- same as other config
- No secrets stored in history

## Next Steps

- Phase 5 uses `get_status()` for enhanced `/agi status`
