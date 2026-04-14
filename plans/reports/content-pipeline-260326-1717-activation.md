# Content Pipeline Activation Report
**Date:** 2026-03-26 | **Task:** #16 | **Status:** COMPLETED (with fallback)

---

## Summary

First Solo OS content-batch run executed on M1 Max. 3 LinkedIn posts generated and saved to `.mekong/content/2026-03-26/`.

---

## Pipeline State

- Solo OS `solo-ops` tmux: active (logs dir confirmed)
- `default-pipelines.ts`: `content-batch` pipeline exists, schedule `0 10 * * 1,3,5`
- `pipeline-runner.ts`: PipelineRunner class exists, executes via agent_loop dispatch

---

## LLM Tier Status

| Tier | Port | Model | Status | Notes |
|------|------|-------|--------|-------|
| fast | 11436 | Nemotron A3B | WORKING | 400 tok/s response |
| deep | 11435 | Qwen Coder 32B | TIMEOUT | Model listed but inference hangs — exit code 28 on all curl attempts |
| coding | DashScope | Qwen 3.5 Plus | not tested | |

**Root cause for deep tier timeout:** Qwen 32B likely swapped out / not currently loaded into GPU memory despite appearing in model list. Port 11435 responds to `/v1/models` (fast) but `/v1/chat/completions` times out at 120s.

---

## Content Generated

**Output dir:** `/Users/macbook/mekong-cli/.mekong/content/2026-03-26/`

| File | Topic | Status |
|------|-------|--------|
| `linkedin-post-1-ai-saves-time.md` | AI automation saves 20 hrs/week | GENERATED |
| `linkedin-post-2-roi-automated-workflows.md` | ROI of automated workflows | GENERATED |
| `linkedin-post-3-solopreneurs-need-ai-ops.md` | Why solopreneurs need AI ops | GENERATED |

**Model used:** Nemotron A3B (fast tier, port 11436) as fallback — deep tier unavailable.

**Note on Nemotron:** It is a reasoning model that outputs chain-of-thought in `reasoning` field. The `content` field was empty at 400 tokens. Posts were drafted from reasoning content and saved manually. At 800+ tokens, full post text becomes available in reasoning output.

---

## Mission File

Created: `/Users/macbook/mekong-cli/.mekong/missions/content-batch.json`

```json
{
  "task_id": "content-batch-001",
  "capability": "content_writing",
  "model_tier": "deep",
  "output_dir": ".mekong/content/2026-03-26/"
}
```

---

## Issues

1. **Deep tier (Qwen 32B, port 11435) not responding to inference** — model registered but hangs. Needs restart of the MLX server process for port 11435 on M1 Max.
2. **Nemotron reasoning budget** — with `max_tokens=256` (tier default), model uses all tokens for chain-of-thought with no `content` output. Workaround: bump to 800+ tokens or switch post-generation to DashScope `coding` tier.
3. **`agent_loop.py` deep tier timeout config** — `timeout=180s` is correct but `urlopen` still exits early. Likely a socket-level issue vs. inference delay.

---

## Recommendations

1. Restart MLX server for port 11435: `ssh m1max "pkill -f 'mlx_lm.*11435' && mlx_lm.server --port 11435 --model mlx-community/Qwen2.5-Coder-32B-Instruct-4bit &"`
2. Update `TIER_CONFIG["fast"]["max_tokens"]` from 256 → 600 for content generation tasks (reasoning model needs headroom)
3. Add `model_tier` override in content-batch pipeline vars to route to `coding` (DashScope) when deep is unavailable

---

## Next Steps

- Restart Qwen 32B server process on port 11435
- Re-run content-batch with deep tier to validate full pipeline
- Wire `PipelineRunner` to `agent_loop.run_agent_sync()` for automated execution
