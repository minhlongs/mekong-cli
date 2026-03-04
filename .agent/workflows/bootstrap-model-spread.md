---
description: "Multi-model parallel bootstrap — round-robin 8 free models across subagents (Max 20x style)"
---

# /bootstrap:model-spread — Parallel Multi-Model Execution

## Strategy: Round-Robin Model Load Balancing

Khi chạy `/bootstrap:auto:parallel`, mỗi subagent sẽ dùng model KHÁC NHAU từ pool 8 models miễn phí. Tránh rate limit, tăng throughput 8x.

## Model Pool (1 API key, 8 models)

| Slot | Model | Vai trò ưu tiên | Context |
|------|-------|-----------------|---------|
| 0 | `qwen3.5-plus` | Main / Planner | 1M |
| 1 | `qwen3-coder-plus` | Coder #1 | 1M |
| 2 | `kimi-k2.5` | Reviewer #1 | 262K |
| 3 | `MiniMax-M2.5` | Researcher | 204K |
| 4 | `glm-5` | Reviewer #2 | 202K |
| 5 | `qwen3-max-2026-01-23` | Planner #2 | 262K |
| 6 | `qwen3-coder-next` | Coder #2 | 262K |
| 7 | `glm-4.7` | Researcher #2 | 202K |

## Execution Steps

### Step 1: Set subagent model via environment
When dispatching subagents, set the model per subagent index:

```bash
# Subagent 0: qwen3.5-plus (default)
# Subagent 1: --model bailian/qwen3-coder-plus
# Subagent 2: --model bailian/kimi-k2.5
# ... round-robin through pool
```

### Step 2: ClaudeKit Command Pattern
When `/bootstrap:auto:parallel` dispatches subagents:

```
Subagent #(N) uses model pool[N % 8]
```

This ensures:
- 10 subagents = max 2 per model (no rate limit)
- 20 subagents = max 3 per model
- 8 subagents = 1 per model (ideal)

### Step 3: Role-Based Assignment
For smarter routing, assign models by subagent role:

- **Planning tasks** → `qwen3.5-plus` or `qwen3-max` (best reasoning)
- **Coding tasks** → `qwen3-coder-plus` or `qwen3-coder-next` (optimized for code)
- **Review tasks** → `kimi-k2.5` or `glm-5` (fresh perspective)
- **Research tasks** → `MiniMax-M2.5` or `glm-4.7` (large output)

### Step 4: Apply to CC CLI panes
For CTO dispatch to 3 panes:

```
P0 (mekong-cli): --model bailian/qwen3.5-plus
P1 (well):       --model bailian/qwen3-coder-plus
P2 (algo):       --model bailian/kimi-k2.5
```

## Benefits
- **0 cost** — all models free on DashScope
- **8x rate limit headroom** — distributed across models
- **Role-optimized** — right model for right task
- **No single point of failure** — if 1 model slow, others compensate
