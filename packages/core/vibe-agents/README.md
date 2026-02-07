# @vibe/vibe-agents

Agent orchestration and management for Vibe platform.

## Installation

```bash
pnpm add @vibe/vibe-agents
```

## Usage

```typescript
import { AgentOrchestrator } from '@vibe/vibe-agents';

const orchestrator = new AgentOrchestrator();
await orchestrator.execute(task);
```

## Features

- Multi-agent coordination
- Task delegation and execution
- Plan-Execute-Verify workflow

## Development

```bash
pnpm build
pnpm dev
```
