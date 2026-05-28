---
name: mlx-inference
description: MLX LLM inference on M1 Max for CashClaw and Mekong CLI. Trigger when working with local LLM servers, model routing, or debugging inference issues. Contains the actual model IDs, ports, and performance characteristics of the two running mlx_lm.server instances. CRITICAL: Docker containers CANNOT access Metal GPU — LLMs must stay bare metal.
---

# MLX Inference on M1 Max

## Overview
Two mlx_lm.server instances run bare metal. Docker containers connect via `host.docker.internal`.

## Running Models

| Model | Port | Speed | RAM | Role |
|---|---|---|---|---|
| DeepSeek-R1-Distill-Qwen-32B-4bit | 11435 | ~10 tok/s | ~3.7 GB | Deep reasoning |
| NVIDIA-Nemotron-3-Nano-30B-A3B-4bit | 11436 | ~45 tok/s | ~2.3 GB | Fast triage |

Server: `mlx_lm.server` (NOT Ollama, NOT Docker Model Runner)
Host: `0.0.0.0`, Python 3.12 Homebrew

## From Docker containers
```
http://host.docker.internal:11435/v1  (DeepSeek R1)
http://host.docker.internal:11436/v1  (Nemotron Nano)
```

## From bare metal
```
http://127.0.0.1:11435/v1
http://127.0.0.1:11436/v1
```

## Scripts
- `scripts/check-llm-health.sh` — Verify both servers respond

## Gotchas
- Docker CANNOT access Metal GPU. Never containerize mlx_lm.server.
- mlx_lm.server serializes requests per-model. Long DeepSeek reasoning blocks other DeepSeek requests.
- Nemotron 3 Nano is MoE (30B total, 3B active). Thinking mode has infinite-loop bug in mlx-lm (Issue #1050). Don't enable `<think>` tags for Nemotron.
- DeepSeek R1 temperature MUST be 0.5-0.7. Above 0.7 = infinite loops. Below 0.5 = repetitive output.
- M1 Max does NOT support BF16 compute natively. MLX converts at runtime — slight overhead.
- Both servers share the same Metal GPU pipeline. Simultaneous queries = halved throughput.
