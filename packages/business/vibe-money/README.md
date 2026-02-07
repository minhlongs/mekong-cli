# @vibe/vibe-money

Financial operations and ledger management for Vibe platform.

## Installation

```bash
pnpm add @vibe/vibe-money
```

## Usage

```typescript
import { DoubleLedger } from '@vibe/vibe-money';

const ledger = new DoubleLedger();
await ledger.recordTransaction(entry);
```

## Features

- Double-entry ledger
- Transaction management
- Financial reporting
- Stripe integration

## Development

```bash
pnpm build
pnpm dev
```
