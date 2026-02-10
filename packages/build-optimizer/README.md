# @mekong/build-optimizer

Build Optimization Loop - Automated build performance monitoring and optimization tool for the Mekong CLI ecosystem.

## Features

- 🔍 **Monitor** - Collect build metrics and track performance over time
- ⚡ **Optimize** - Automatically apply optimization strategies
- 🧪 **Test** - Validate optimizations don't break functionality
- 🚀 **Deploy** - Deploy optimized builds with confidence

## Installation

```bash
npm install @mekong/build-optimizer
# or
pnpm add @mekong/build-optimizer
```

## Usage

### Programmatic API

```typescript
import { loadConfig, createLogger } from '@mekong/build-optimizer';

const config = await loadConfig({ verbose: true });
const logger = createLogger({ verbose: true });

logger.info('Starting optimization loop', { apps: config.apps.length });
```

### Configuration

Create a `mekong.config.js` file:

```javascript
export default {
  optimization: {
    apps: [
      {
        name: 'web-app',
        path: './apps/web',
        type: 'nextjs',
        buildCommand: 'npm run build',
        outputDir: '.next',
        budget: {
          maxBundleSize: 500,
          maxBuildTime: 120,
        },
      },
    ],
    thresholds: {
      bundleSizeWarning: 400,
      bundleSizeError: 600,
      buildTimeWarning: 90,
      buildTimeError: 180,
    },
    strategies: {
      treeShaking: true,
      codeSplitting: true,
      compression: true,
      caching: true,
    },
    monitoring: {
      enabled: true,
    },
  },
};
```

### Environment Variables

- `MEKONG_MONITORING_ENABLED` - Enable/disable monitoring
- `MEKONG_MONITORING_ENDPOINT` - Custom monitoring endpoint
- `MEKONG_TREE_SHAKING` - Enable/disable tree shaking
- `MEKONG_CODE_SPLITTING` - Enable/disable code splitting
- `MEKONG_COMPRESSION` - Enable/disable compression
- `MEKONG_CACHING` - Enable/disable caching

## Configuration Priority

1. CLI flags
2. Environment variables
3. Local config file (`.mekongrc`, `mekong.config.js`)
4. Global config (`~/.config/mekong/config.json`)
5. Default values

## Development

```bash
# Install dependencies
pnpm install

# Build
pnpm build

# Development mode
pnpm dev

# Run tests
pnpm test
```

## License

MIT
