# @vibe/vibe-crm

CRM integration and customer management for Vibe platform.

## Installation

```bash
pnpm add @vibe/vibe-crm
```

## Usage

```typescript
import { CRMClient } from '@vibe/vibe-crm';

const crm = new CRMClient();
await crm.syncCustomers();
```

## Features

- CRM integration
- Customer data management
- Contact synchronization
- Lead tracking

## Development

```bash
pnpm build
pnpm dev
```
