# Mekong CLI — Docker Environment

> "Hoàn nguyên bổn thể" — Soul meets body

Containerized AI agent workstation based on [HolyClaude](https://github.com/CoderLuii/HolyClaude) patterns, adapted for Mekong CLI's PEV pipeline.

## Quick Start

```bash
cd docker
docker compose up -d
# Open http://localhost:3001 (Claude Code UI)
# API at http://localhost:8000 (Mekong Gateway)
```

## What's Inside

| Component | Purpose |
|-----------|---------|
| Claude Code CLI | AI coding agent |
| CloudCLI | Browser-based web UI (port 3001) |
| Mekong Gateway | FastAPI RaaS API (port 8000) |
| Chromium + Xvfb | Headless browser for Playwright |
| s6-overlay | Process supervision (auto-restart) |
| Apprise | Push notifications (100+ services) |
| 50+ dev tools | ripgrep, fzf, bat, tmux, gh, etc. |

## Architecture

Based on HolyClaude's battle-tested patterns:
- s6-overlay as PID 1 (not supervisord)
- Sentinel-based first-boot bootstrap
- CLAUDE.md memory injection
- UID/GID remapping for host permissions
- Multi-arch (AMD64 + ARM64)

## Notifications

Enable push notifications for PEV pipeline events:

```bash
# Inside container
touch ~/.claude/notify-on

# In docker-compose, set:
NOTIFY_DISCORD=discord://webhook_id/webhook_token
```

Events: `cook.done`, `verify.pass`, `verify.fail`, `error`

## Credits

- [HolyClaude](https://github.com/CoderLuii/HolyClaude) by CoderLuii — Docker patterns, s6-overlay architecture
- [Binh Phap Venture Studio](https://binhphap.io) — Mekong CLI, PEV engine, RaaS billing
