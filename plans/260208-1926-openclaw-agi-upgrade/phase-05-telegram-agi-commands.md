# Phase 5: Telegram Bot AGI Commands

## Context Links

- Source: `/Users/macbookprom1/mekong-cli/src/core/telegram_bot.py` (710 lines)
- Depends on: Phase 3 (`get_status()` method on AGILoop)

## Overview

- **Priority**: P2
- **Status**: pending
- **Effort**: 1h

Enhance `/agi status` with rich metrics, add `/agi history` command, add `/agi config` command, and update HELP_TEXT.

## Key Insights

- Current `/agi status` (lines 340-349): only shows running/stopped, iteration count, improvement count, consecutive failures
- Phase 3 adds `get_status()` returning: running, iteration, improvements, consecutive_failures, success_rate, uptime_seconds, last_improvement, cooldown
- History data available from `~/.mekong/agi_history.json` (Phase 3)
- HELP_TEXT (lines 44-57) doesn't mention `/agi`, `/remember`

## Requirements

- `/agi status` shows success rate %, uptime, last improvement title, current cooldown
- `/agi history` shows last 5 improvements with status and timestamp
- `/agi config` shows current cooldown and max_iterations settings
- HELP_TEXT updated with AGI and memory commands

## Architecture

No new files. Extend `agi_handler()` in `MekongBot` with subcommand routing: status/start/stop/history/config.

## Related Code Files

- **Modify**: `src/core/telegram_bot.py`

## Implementation Steps

1. Update HELP_TEXT (lines 44-57) to include AGI commands:
   ```python
   HELP_TEXT = """... (existing content) ...

   *AGI Self-Improvement:*
   /agi start — Start AGI loop
   /agi stop — Stop AGI loop
   /agi status — Detailed AGI metrics
   /agi history — Last 5 improvements
   /agi config — Show AGI configuration

   *Memory:*
   /remember <content> — Store memory
   """
   ```

2. Refactor `agi_handler()` (lines 300-353). Replace the `else: # status` block (lines 340-349) with call to `get_status()`:
   ```python
   else:  # status
       status = agi.get_status()
       running_str = "Running" if status["running"] else "Stopped"
       running_icon = "🟢" if status["running"] else "🔴"

       uptime_min = status["uptime_seconds"] // 60
       uptime_str = f"{uptime_min // 60}h {uptime_min % 60}m" if uptime_min >= 60 else f"{uptime_min}m"

       last_title = "N/A"
       if status.get("last_improvement"):
           last_title = status["last_improvement"].get("title", "N/A")

       await update.message.reply_text(
           f"♾️ *AGI Loop Status*\n\n"
           f"{running_icon} {running_str} | Iteration #{status['iteration']}\n"
           f"━━━━━━━━━━━━━━━━━━━━\n"
           f"📊 Success: {status['improvements']}/{status['iteration']} ({status['success_rate']}%)\n"
           f"⏱ Uptime: {uptime_str}\n"
           f"🎯 Last: \"{last_title}\"\n"
           f"❌ Consecutive fails: {status['consecutive_failures']}\n"
           f"😴 Cooldown: {status['cooldown']}s",
           parse_mode="Markdown",
       )
   ```

3. Add `history` subcommand in `agi_handler()` (before the `else` block):
   ```python
   elif action == "history":
       import json
       from pathlib import Path
       history_path = Path.home() / ".mekong" / "agi_history.json"
       if not history_path.exists():
           await update.message.reply_text("No AGI history yet.", parse_mode="Markdown")
           return
       try:
           history = json.loads(history_path.read_text())
           details = history.get("details", [])[-5:]
           if not details:
               await update.message.reply_text("No improvements recorded yet.", parse_mode="Markdown")
               return
           lines = ["📜 *AGI History (Last 5)*\n"]
           for d in reversed(details):
               icon = "✅" if d.get("success") else "❌"
               ts = time.strftime("%m/%d %H:%M", time.localtime(d.get("timestamp", 0)))
               lines.append(f"{icon} `{d.get('id', '?')}` — {d.get('title', '?')}\n   {ts} | {d.get('category', '?')}")
           await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
       except Exception as e:
           await update.message.reply_text(f"Error reading history: {e}", parse_mode="Markdown")
   ```

4. Add `config` subcommand in `agi_handler()`:
   ```python
   elif action == "config":
       await update.message.reply_text(
           f"⚙️ *AGI Configuration*\n\n"
           f"Cooldown: {agi.cooldown}s (adaptive)\n"
           f"Max iterations: {agi.max_iterations or 'unlimited'}\n"
           f"Telegram notify: {agi.telegram_notify}\n"
           f"Max consecutive failures: {agi.MAX_CONSECUTIVE_FAILURES}",
           parse_mode="Markdown",
       )
   ```

5. Ensure `import time` is available at module level (already imported at line 20)

## Todo List

- [ ] Update HELP_TEXT with AGI and memory commands
- [ ] Refactor `/agi status` to use `get_status()` with rich formatting
- [ ] Add `/agi history` subcommand
- [ ] Add `/agi config` subcommand
- [ ] Run `python3 -m pytest tests/ -v` -- all tests pass

## Success Criteria

- `/agi status` shows: running state, iteration, success rate %, uptime, last improvement title, cooldown
- `/agi history` shows last 5 improvements with icons, timestamps, categories
- `/agi config` shows current settings
- HELP_TEXT lists all AGI and memory commands

## Risk Assessment

- **History file read race**: AGI loop writes while Telegram reads. Risk: low (JSON read is atomic enough for this size). If corruption occurs, caught by try/except
- **Long messages**: History with 5 entries stays well under Telegram's 4096 char limit

## Security Considerations

- No new permissions or secrets
- History data read-only from Telegram handler

## Next Steps

- All 5 phases complete. Run full test suite to verify no regressions.
