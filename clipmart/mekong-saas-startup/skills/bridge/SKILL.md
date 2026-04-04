---
name: bridge
description: "Unified bridge for all AgencyOS CLI tools"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: Unified bridge for all AgencyOS CLI tools
---

# Bridge Command

Điều khiển tất cả AgencyOS bridges qua 1 entry point.

```
🏯 "Dễ như ăn kẹo" - Easy as candy!
```

## Quick Commands

```bash
# Check status
/bridge:status

# Gemini integration
/bridge:gemini ask "Your question"
/bridge:gemini vision ./image.png
/bridge:gemini code ./file.js

# Git worktree
/bridge:git create my-feature
/bridge:git list
/bridge:git remove my-feature

# Python antigravity
/bridge:antigravity dna
/bridge:antigravity content 10
```

## Usage

### Check Status
// turbo
```bash
node .claude/scripts/agencyos-bridge.cjs status
```

### Ask Gemini
// turbo
```bash
node .claude/scripts/agencyos-bridge.cjs gemini ask "How to optimize React?"
```

### Create Git Worktree
// turbo
```bash
node .claude/scripts/agencyos-bridge.cjs git create my-feature
```

### Quick Start
// turbo
```bash
node .claude/scripts/agencyos-bridge.cjs quickstart
```

## Features

| Feature | Description |
|---------|-------------|
| 🔄 Rate Limiting | 15 requests/minute (shared) |
| ♻️ Auto Retry | Exponential backoff |
| 📊 Status Dashboard | Unified monitoring |
| 🎯 Single Entry | 1 command for all |

## 🏯 Binh Pháp

> "Không đánh mà thắng" - Win Without Fighting

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
