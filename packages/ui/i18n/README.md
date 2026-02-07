# @vibe/i18n

Internationalization (i18n) utilities for Vibe applications.

## Installation

```bash
pnpm add @vibe/i18n
```

## Usage

```typescript
import { t, setLocale } from '@vibe/i18n';

setLocale('en');
const message = t('common.welcome');
```

## Features

- Multi-language support
- Type-safe translation keys
- Locale switching utilities

## Development

```bash
pnpm build
pnpm dev
```
