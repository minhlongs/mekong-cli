# C2 — TUI Streaming UX — Implementation Report

**Date:** 2026-07-13 16:40
**Status:** DONE
**Component:** Phase C2 — TUI Streaming UX

## What was built

### 1. `cli/tui/streaming.py` (new, 540 lines)

**`StreamingRenderer`** — the core streaming display engine:
- Subscribes to `StreamingEventBus` event types (`STEP_STARTED`, `STEP_COMPLETED`, `STEP_FAILED`, `STEP_HEALED`, `GOAL_COMPLETED`, `HALT_TRIGGERED`).
- Uses Rich `Live` display with 10fps refresh — terminal updates in real-time, no batch dump.
- Two-panel layout: progress bar + per-step status on top, streaming agent output on bottom.
- Output buffer capped at 500 lines (FIFO eviction).
- Cancel support: `cancel()` public method + Ctrl-C handling → emits `HALT_TRIGGERED` on bus + optional user callback.
- Thread-safe event handling (event bus is synchronous; Live runs on caller's thread).

**`ProgressPanel`** — progress tracking widget:
- Rich `Progress` bar (text + bar + completed/total + elapsed time).
- Per-step status list (pending/running/success/error/skipped) with Unicode icons and duration.
- Methods: `add_step`, `start_step`, `complete_step`, `cancel_step`, `render`.
- Uses `dataclasses.replace` (not `_replace` — removed in Python 3.14).

**`StreamingSession`** — convenience context manager:
- Starts renderer in a daemon thread, lets caller do real work in the `with` block.
- Propagates `register_step`, `add_output`, `set_total_steps`.

### 2. Tests: `tests/test_tui_streaming.py` (43 tests, all pass)

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestOutputLine` | 3 | Default fields, custom fields, frozen |
| `TestStepProgress` | 2 | Default fields, custom status |
| `TestProgressPanel` | 6 | Add/start/complete/cancel/render/no-crash |
| `TestStreamingRendererEvents` | 8 | All event types, stdout injection, halt/goal stop |
| `TestStreamingRendererOutput` | 7 | Add, eviction, mark, max_lines constant |
| `TestStreamingRendererLifecycle` | 7 | State, steps, cancel callback, halt emission |
| `TestStreamingRendererCleanup` | 3 | Unsubscribe, empty subscribed_types, live null |
| `TestStreamingRendererRender` | 2 | Layout type, panel names (progress + output) |
| `TestStreamingSession` | 4 | Context manager, propagation tests |

```
43 passed in 0.34s
```

## Integration points

- **Deliverable 1 (real-time streaming):** `StreamingRenderer.start()` opens `Live` display; `_on_event` callback updates output and progress panels on every bus event. Old behavior: step output was printed after execution completed (in `executor.py` console prints). New behavior: step output streams via `add_output()` which is called from event handlers.
- **Deliverable 2 (ProgressPanel):** `ProgressPanel` tracks step state transitions. Integrated into `StreamingRenderer._render()` as the top layout region.
- **Deliverable 3 (Cancel support):** `StreamingRenderer.cancel()` → `_handle_cancel()` → fires cancel callback + emits `EventType.HALT_TRIGGERED` on bus → state transitions to `STOPPED` → Live loop exits.

## Design decisions

- Python 3.14 compat: replaced `dataclass._replace()` with `dataclasses.replace()` (removed in 3.14).
- `frozen=True` on dataclasses for immutability — use `dataclasses.replace` for updates.
- `ProgressPanel.render()` uses `rich.console.Group` instead of `Text.append(Panel)` (the latter was a TypeError in test).
- Cancel emits `HALT_TRIGGERED` (not `GOAL_CANCELLED`) — matches existing event type in event bus.

## Unresolved questions

1. **Executor integration:** `RecipeExecutor._execute_shell_step` currently does `self.console.print(Panel(...))` for each step. Should executor push output into `StreamingRenderer` via `add_output()` instead, or should a thin adapter layer handle that?
2. **Live display + tmux:** The existing `TmuxLauncher` creates 3-pane layout (palette | block history | raw output). Does `StreamingRenderer` replace the raw output pane, or do they coexist?
