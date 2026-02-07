# @vibe/vibe-bridge

Integration bridge for external services and APIs.

## Installation

```bash
pnpm add @vibe/vibe-bridge
```

## Usage

```typescript
import { Bridge } from '@vibe/vibe-bridge';

const bridge = new Bridge();
await bridge.connect(service);
```

## Features

- Service integration
- API connectors
- Data transformation
- Webhook handling

## Development

```bash
pnpm build
pnpm dev
```
