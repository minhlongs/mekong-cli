import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/sdk.ts'],
  format: ['esm', 'cjs'],
  dts: true,
  clean: true,
  outDir: 'dist',
});
