# mekongd — Qwen3.6 Local Daemon for CC CLI

Cuts Claude Code API bill 4-10x by routing cheap subagent work (explore/search/reformat) to local Qwen3.6-35B-A3B on Apple Silicon, while keeping Opus for planning & review.

## Why

- **Heavy CC CLI users** burn $200-500/mo on Anthropic API for cheap lookups
- **Qwen3.6-35B-A3B** scores SWE-bench 73.4, Terminal-Bench 51.5 — good enough for ~70% of subagent work
- **M1 Max 64GB** runs Q4 quantized model at ~30 tok/s, uses only ~20GB RAM
- **Anthropic-compat proxy** = drop-in replacement, zero code changes in CC CLI

## Install

```bash
# Non-Apple-Silicon (dev / CI)
poetry install

# Apple Silicon (production)
poetry install --with mlx
```

## Run

```bash
# Serve Anthropic-compat proxy on localhost:8765
poetry run mekongd serve

# Inspect stats
poetry run mekongd stats show

# View config
poetry run mekongd config show

# View metrics (Prometheus format)
curl http://127.0.0.1:8765/metrics
```

## Point CC CLI at mekongd

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8765
claude
```

## Status

**v0.1.0** — MVP scaffold. Local MLX + SSE streaming + regex router + SQLite stats. Production hardening and cloud fallback in v0.2.

## License

MIT
