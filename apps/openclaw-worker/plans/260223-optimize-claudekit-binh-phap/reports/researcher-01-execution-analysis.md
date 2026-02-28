# Execution Analysis: Binh Phap Rules & ClaudeKit Commands

## Executive Summary
This report analyzes why Binh Phap rules and ClaudeKit slash commands (e.g., `/cook`, `/plan:parallel`) in `apps/openclaw-worker` occasionally fail to trigger their full intended workflows. The investigation focused on prompt construction (`mission-dispatcher.js`) and CLI execution (`brain-process-manager.js`).

## Core Finding: Thermal Downgrade (Hàn Băng Mode)
The primary reason advanced commands like `/plan:parallel` are bypassed is the **Active Thermal Management (Hàn Băng Mode)** in `mission-dispatcher.js`.

When system load is critical, advanced commands are intentionally stripped:
```javascript
// From lib/mission-dispatcher.js
if (load > 30) {
  log(`⚠️ THERMAL CRITICAL (Load ${load}): Downgrading to minimal parallel /cook`);
  return formatCmd('/cook', safe + ' Nhiệt cao nhưng PHẢI dùng ít nhất 3 subagents parallel.', '--parallel --auto');
}
```
**Impact:** Instead of deep planning or complex multi-agent Binh Phap strategies, the system defaults to a basic `/cook` to preserve CPU/RAM.

## Execution Finding: Dropped Inputs in Tmux
The second failure mode lies in how commands are fed to the Claude CLI inside the Tmux session managed by `brain-process-manager.js`.

1. **Disabled Kick-Start:** The orchestration relies on pasting text into Tmux and sending an `Enter` keystroke. However, the failsafe to re-send the Enter key if the process stalls was disabled to prevent duplicate tasks:
```javascript
// From lib/brain-process-manager.js
// KICK-START: DISABLED — was root cause of x2 dispatch bug!
// sendEnter() re-submitted the already-pasted prompt, creating duplicate tasks.
```
**Impact:** If Tmux drops the initial `Enter` keystroke or the CLI is sluggish in receiving it, the prompt just sits on the terminal line forever. The polling loop (`state === 'idle'`) will eventually time out or misclassify the state, causing the mission to fail silently without executing.

## State Detection Fragility
The orchestrator tracks execution by polling Tmux output and matching regex patterns:
- `BUSY_PATTERNS`: Identifies if Claude is thinking or reading.
- `COMPLETION_PATTERNS`: Identifies if the prompt returned (e.g., `❯`).

**Impact:** If ClaudeKit updates its UI (e.g., changing spinner text or formatting), the regexes might fail to trigger `isBusy = true`. The system might incorrectly assume the process finished instantly or failed, missing the execution window. Additionally, automated prompts (like answering "2" for API keys) can stall if the prompt text changes slightly.

## Recommendations
1. **Dynamic Kick-Start:** Re-enable kick-start but make it smarter. Instead of resending the whole prompt, strictly send an empty `\n` if the state remains `idle` with text sitting on the prompt line.
2. **Thermal Visibility:** Expose the `load` status in the mission logs so users clearly see when a task was downgraded due to "Hàn Băng Mode".
3. **UI Agnostic Polling:** Reduce reliance on exact text matching for `BUSY_PATTERNS`. Instead, monitor process CPU usage or the presence of the `claude` child process to determine if it is actively working.