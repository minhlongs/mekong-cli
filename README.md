# Mekong CLI

[![CI](https://github.com/longtho638-jpg/mekong-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/longtho638-jpg/mekong-cli/actions/workflows/ci.yml)
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-6.0.0-green)](VERSION)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)

**Describe your goal. AI plans, executes, verifies, delivers.**

Mekong CLI is an AI-operated business platform. One command triggers multi-agent workflows that build software, run marketing, manage finances, and ship products — powered by any LLM.

<!-- TODO: Add demo GIF here -->
<!-- ![Demo](docs/assets/demo.gif) -->

## Quick Start

```bash
# Clone and setup
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli && source scripts/shell-init.sh

# Set any OpenAI-compatible LLM (3 env vars)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4

# Run your first command
mekong cook "Create a REST API with auth"
```

**Free with local LLM:**

```bash
ollama pull qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434/v1
mekong cook "Create a Python calculator"
```

## What It Does

- **Plan → Execute → Verify** — AI decomposes goals into steps, executes them, self-heals on failure
- **300+ Commands** across 5 business layers (founder, business, product, engineering, ops)
- **Universal LLM** — works with OpenRouter, Anthropic, OpenAI, DeepSeek, Ollama, or any OpenAI-compatible API
- **DAG Workflows** — parallel multi-agent execution with dependency graphs
- **$0 Infrastructure** — deploys on Cloudflare Workers + D1 + Pages (free tier)

## 5 Business Layers

```
Founder      /annual /okr /fundraise /swot         — Strategy
Business     /sales /marketing /finance /hr         — Revenue
Product      /plan /sprint /roadmap /brainstorm     — Product
Engineering  /cook /code /test /deploy /review      — Build
Ops          /audit /health /security /status       — Monitor
```

## Example: Multi-Agent Workflow

```bash
$ mekong founder:raise "Series A for AI platform"
  Group 1 (parallel): /unit-economics + /tam + /moat-audit
  Group 2 (parallel): /financial-model + /data-room
  Group 3 (sequential): /cap-table → /pitch → /vc-map
  Output: reports/raise-ready-kit/
```

## Architecture

```
CLI (mekong cook/fix/plan/deploy)
    │
    ▼
PEV Engine (Plan → Execute → Verify)
    │
    ▼
Agent Layer (GitAgent, FileAgent, ShellAgent, ...)
    │
    ▼
LLM Router (3 env vars → any provider)
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [Command Reference](docs/command-reference.md)
- [API Documentation](docs/api-reference.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [QUICKSTART.md](QUICKSTART.md).

## License

[BSL 1.1](LICENSE) — changes to MIT on 2028-03-13.
