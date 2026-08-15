# LLM Provider Keys Setup Guide

Generate an OpenRouter key for the shared backend key, then use
the standard provider API key on the device actually running inference.

## Flow

OpenRouter key -> backend routing. Provider API key -> on-device inference.

OpenRouter only sees requests; it does not hold your provider secret
and cannot use your downstream quota.

## Setup

| Step | Location | Action |
|------|----------|--------|
| 1 | openrouter.ai/keys | Create an API key |
| 2 | mekong config | Store as OPENROUTER_API_KEY or LLM_API_KEY |
| 3 | Target device | Store provider API key locally only |

## Security Rules

- DO NOT commit any API key in plaintext
- DO NOT add .env to git
- DO NOT expose OPENROUTER_API_KEY to the inference device
- DO store the target-device provider API key only on that device
- DO back up OpenRouter key via a secrets manager
- DO use environment variables managed outside of git
- DO reference OPENROUTER_API_KEY in docs instead of naming the literal value

## Key Responsibilities

OpenRouter key owner is responsible for:
- Key rotation on compromise
- Monitoring usage via openrouter.ai/activity
- Revoking keys when team members leave

Target-device provider key owner is responsible for:
- Never transmitting the key off-device
- Rotating if device access is lost
- Keeping the key out of logs and crash reports

## Environment Variables

| Variable | Purpose | Where set |
|----------|---------|-----------|
| OPENROUTER_API_KEY | OpenRouter routing key (shared) | Backend/CI only |
| LLM_API_KEY | Backwards-compat alias for OpenRouter | Backend/CI only |
| LLM_BASE_URL | API endpoint | Everywhere |
| LLM_MODEL | Model ID | Everywhere |
| OPENAI_API_KEY | OpenAI direct key | Inference device only |
| ANTHROPIC_API_KEY | Anthropic direct key | Inference device only |
| DEEPSEEK_API_KEY | DeepSeek direct key | Inference device only |
| DASHSCOPE_API_KEY | DashScope direct key | Inference device only |
