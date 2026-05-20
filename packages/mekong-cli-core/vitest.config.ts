import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts', 'tests/**/*.test.ts'],
    coverage: {
      reporter: ['text', 'json', 'html'],
    },
  },
  resolve: {
    alias: {
      '@openclaw/cli-adapter': path.resolve(__dirname, '../cli-adapter/dist/index.js'),
      '@mekong/raas-sdk': path.resolve(__dirname, '../raas-sdk/src/index.ts'),
      '@mekongcli/openclaw-engine': path.resolve(__dirname, '../openclaw-engine/src/sdk.ts'),
    },
  },
});
