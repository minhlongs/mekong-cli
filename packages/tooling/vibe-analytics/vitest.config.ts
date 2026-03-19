import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["**/*.{test,spec}.ts"],
    exclude: ["**/*.js", "**/node_modules/**", "**/dist/**"],
  },
});
