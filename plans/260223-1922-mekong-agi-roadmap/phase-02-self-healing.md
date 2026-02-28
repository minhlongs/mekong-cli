# Phase 02 — Self-Healing Auto-Correct Integration

**Context:** [plan.md](plan.md) | [audit-results.md](research/audit-results.md)

## Overview
- **Date:** 2026-02-23
- **Priority:** P1 (AGI core capability)
- **Status:** pending
- **Effort:** 2h
- **Blocked by:** Phase 01

## Key Insights
- `self_improve.py`: `SelfImprover.analyze_and_improve()` EXISTS — nhưng không được gọi trong main orchestration loop
- `orchestrator.py` có `self_healed: bool = False` trong `StepResult` — field exists nhưng chưa được set
- `executor.py` có `_execute_shell_step` — cần thêm LLM-powered auto-fix khi step fail
- Pattern: failed step → LLM analyze error → suggest corrected command → retry

## Requirements
- Khi shell step fail với exit_code ≠ 0:
  - LLM phân tích stderr + suggest corrected command
  - Retry tối đa 2 lần với corrected command
  - Set `StepResult.self_healed = True` khi fix thành công
- `SelfImprover.analyze_and_improve()` phải được gọi sau mỗi orchester session

## Related Files
- `src/core/self_improve.py` — SelfImprover class (partial)
- `src/core/executor.py` — `_execute_shell_step()` (add retry logic here)
- `src/core/orchestrator.py` — `run_from_recipe()` (add post-session improve call)
- `tests/test_self_healing.py` — existing tests để validate

## Architecture
```
Shell Step FAIL
    ↓
executor._execute_shell_step detects exit_code ≠ 0
    ↓
llm_client.chat(f"Fix this bash error: {stderr}") → corrected_cmd
    ↓
Retry with corrected_cmd (max 2 attempts)
    ↓
If success: StepResult.self_healed = True
    ↓
Post-session: SelfImprover.analyze_and_improve()
```

## Implementation Steps

1. **executor.py** — thêm LLM-powered retry trong `_execute_shell_step`:
   ```python
   if result.exit_code != 0 and self.llm_client:
       corrected = self._llm_correct_command(step.command, result.stderr)
       if corrected:
           result = self._run_shell(corrected)
           result.metadata["self_healed"] = True
   ```

2. **orchestrator.py** — set `step_result.self_healed` khi executor signals healed:
   ```python
   step_result.self_healed = execution.metadata.get("self_healed", False)
   ```

3. **orchestrator.py** — thêm post-session `analyze_and_improve()`:
   ```python
   # After memory.record(entry):
   if hasattr(self, 'self_improver'):
       self.self_improver.analyze_and_improve()
   ```

4. Verify với `tests/test_self_healing.py`

## Todo
- [ ] Đọc đầy đủ `self_improve.py` để hiểu current impl
- [ ] Thêm LLM retry vào `executor._execute_shell_step`
- [ ] Wire `self_healed` flag trong orchestrator
- [ ] Gọi `analyze_and_improve()` post-session
- [ ] Chạy `test_self_healing.py` — xác nhận pass

## Success Criteria
- Failed shell command → LLM suggests fix → retry → `self_healed=True`
- `test_self_healing.py` 100% pass
- `SelfImprover` được call sau mỗi session

## Risk
- Medium: cần LLM online để test; cần mock trong tests
- `self_improve.py` có thể đã có logic này — verify trước khi implement

## Files Sẽ Sửa (max 5)
1. `src/core/executor.py`
2. `src/core/orchestrator.py`
3. `src/core/self_improve.py` (nếu cần)

## Next Steps
→ Phase 03: NLU Enhancement
