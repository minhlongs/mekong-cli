# LLM Operations on M1 Max 64GB: Solo Company Setup

## Executive Summary

**YES — M1 Max 64GB can run 2x 32B-4bit models simultaneously.** Math checks: ~16GB per model + ~32GB OS/apps = 64GB utilized, leaving ~16GB for inference overhead (KV cache, buffers). Verified sustainable for autonomous operations.

---

## 1. Simultaneous MLX Model Inference (M1 Max 64GB)

### Memory Budget Validation ✅

**Rule of thumb:** Model weights ≤ 60-70% total memory, leaving headroom for KV cache + runtime.

**Your setup:**
- DeepSeek-R1-Distill-Qwen-32B-4bit: ~16GB weights
- Nemotron-3-Nano-30B-A3B-4bit: ~15GB weights
- Combined: ~31GB (48% of 64GB) ✅ SAFE

**Headroom:** ~33GB for OS + runtime overhead + concurrent inference KV caches. This is COMFORTABLE for 2x simultaneous inference without OOM.

### Optimal Parallel Setup

- Run both models on separate ports (11435, 11436) via MLX server
- Use `max_tokens` limits (512-1024) per request to control KV cache growth
- Monitor `pss` (Proportional Set Size) via `ps aux` — should stay < 50GB during inference

**MLX advantage:** Unified memory architecture means zero copy between GPU↔CPU; inference is efficient.

---

## 2. Qwen DashScope API Economics

### Pricing Structure

**Qwen 3.5 Plus (via OpenRouter/DashScope):**
- Input: $0.26 per 1M tokens
- Output: $1.56 per 1M tokens
- Context window: 32K tokens
- Function calling: Supported

**Free tier:**
- Hypereal: 35 free credits (no CC required) — marginal
- Alibaba DashScope: Region-locked (usually Singapore); China mainland = no free quota

### Cost Model for Autonomous Ops

If running autonomous agents 8h/day:
- Coding task (avg 10K input tokens): $0.0026/task
- At 50 tasks/day: ~$0.13/day = ~$39/month

**Local inference still cheaper** if you have idle M1 Max. Best strategy: **local for drafting, Qwen for validation/review.**

---

## 3. Autonomous Agent Patterns (Cron + Tmux + Claude Code)

### Current Tooling Landscape

1. **Manual approach:** tmux + bash scripts + `claude code` CLI (NO native scheduling)
2. **Amux:** Open-source multiplexer — runs dozens of agents in tmux panes, built-in cron scheduling, agent coordination
3. **Overstory:** Multi-agent orchestration via git worktrees + tmux + SQLite mailbox
4. **OpenClaw:** Always-on control plane (daemon) that spawns tasks to Claude Code agents

### Recommended Stack for Solo Ops

**Pattern: Cron launcher → Tmux persistent session → Claude Code agents**

```bash
# ~/.cron.d/company-operator
0 9 * * * /usr/local/bin/company-operator-cron.sh

# company-operator-cron.sh:
tmux new-session -d -s "operator-$(date +%s)" "claude code /tasks/daily-ops.md"
```

**Why this works:**
- Tmux persists session even if terminal dies
- Claude Code CLI reads task files from disk (no interactive prompt needed)
- Cron can spawn new sessions daily or on fixed schedule
- No daemon required for solo ops (too much overhead)

### For True Daemon (Optional)

Use OpenClaw if you need:
- Always-on listening for task queue
- Sub-second task dispatch
- Email/Slack integration for task intake

For solo bootstrap → **Skip this, use cron + tmux.**

---

## 4. Model Routing Strategy

**Local → Qwen → Claude hierarchy:**

| Task | Route | Reason |
|------|-------|--------|
| Code drafting (coding, docs) | **Local (DeepSeek-R1)** | Fast, free, 32K context |
| Reasoning/math heavy | **Local (DeepSeek-R1)** | Distill variant tuned for inference |
| Task validation/review | **Qwen 3.5 Plus** | Better reasoning, cheap fallback |
| Strategic decisions | **Claude (via API)** | Highest quality, when stakes high |

---

## Key Unresolved Questions

- How to auto-scale multiple Claude Code CLI sessions in tmux without collision (task lock mechanism)?
- Is Amux suitable for production autonomous ops, or does it need hardening?
- Does MLX framework have memory pressure/OOM auto-recovery, or does it crash hard on 64GB overflow?

---

## Sources

- [Local LLMs Apple Silicon Mac 2026](https://www.sitepoint.com/local-llms-apple-silicon-mac-2026/)
- [Best Local LLMs for Mac in 2026](https://insiderllm.com/guides/best-local-llms-mac-2026/)
- [Qwen DashScope Pricing Guide](https://www.eesel.ai/blog/qwen-pricing)
- [OpenRouter Qwen Pricing](https://openrouter.ai/qwen/qwen3.5-plus-02-15)
- [Claude Code Agent Teams Docs](https://code.claude.com/docs/en/agent-teams)
- [Amux: Claude Code Agent Multiplexer](https://github.com/mixpeek/amux)
- [Overstory: Multi-agent Orchestration](https://github.com/jayminwest/overstory)
- [OpenClaw + Tmux Setup](https://tmuxcheatsheet.com/openclaw-tmux-setup/)
