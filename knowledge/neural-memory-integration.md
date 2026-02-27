# Neural Memory Integration (Spreading Activation)
Date: 2026-02-23

## Overview
This document records the installation and integration of `neural-memory` as the primary brain-like persistent memory for the OpenClaw AI ecosystem (bypassing the initially proposed Mem0 architecture).

### Key Upgrades:
- **Spreading Activation**: Replaces standard RAG/Vector search with biological-style neural associations.
- **Vietnamese NLP**: Full native support for Tiếng Việt (`nlp-vi` plugin).
- **Universal Distribution**: Configured to be shared across Antigravity Proxy, Cursor, VS Code, and CC CLI (`mcpServers.neural-memory`).
- **Hook Automation**: `nmem hooks install` enabled to automatically capture Git diffs as commit context for AI.

## Binh Pháp Mapping
**始計 THỦY KẾ** — Bộ nhớ thần kinh = não bộ của toàn quân đội. Nhớ dai, liên tưởng, chia sẻ tri thức qua MCP trên mọi mặt trận (Tướng Tiên Phong, Antigravity, Editor).

## Status:
- MCP Configured (`nmem-mcp` added to `~/.gemini/settings.json`)
- CC CLI: Connected via `neural-memory@neural-memory-marketplace` plugin.
- Brain File: `~/.neural_memory/tomhum-brain.db`
