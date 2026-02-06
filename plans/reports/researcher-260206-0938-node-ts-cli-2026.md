# Research Report: Modern Node.js/TypeScript CLI Frameworks (2026)

**Date:** 2026-02-06
**Status:** Final
**Author:** Researcher Agent (Antigravity)

## 1. Executive Summary: The 2026 "Golden Stack"

For a robust, type-safe, and user-friendly CLI in 2026, the industry has converged on a stack that balances performance (startup time) with Developer Experience (DX).

| Component | Recommendation | Why? |
| :--- | :--- | :--- |
| **Framework** | **Commander.js** (w/ Zod) | Standard, vast ecosystem, stable. |
| **Alternative** | **Citty** (UnJS) | Best for ESM-native, lightweight, fast startup. |
| **Enterprise** | **Oclif** | If building a plugin architecture (e.g., Salesforce, Heroku style). |
| **Prompts** | **@clack/prompts** | Superior UX, minimal aesthetic, better than Inquirer. |
| **Styling** | **Picocolors** | 10x smaller/faster than Chalk. |
| **Spinners** | **Ora** | Still the gold standard for async feedback. |
| **Config** | **c12** | Smart config loading (rc files, .config.ts, defaults). |
| **Testing** | **Vitest** + **Execa** | Native ESM support, fast, robust process spawning. |
| **Bundler** | **Unbuild** / **Tsup** | Zero-config compilation to ESM/CJS. |

---

## 2. Framework Landscape Analysis

### Option A: Commander.js (The Standard)
Still the safe default. In 2026, typically paired with `zod` for argument parsing validation.
*   **Pros:** Massive community, extensive plugins, recognizable API.
*   **Cons:** Boilerplate heavy for complex commands, large bundle size if not careful.
*   **Best For:** General purpose tools, rapid development.

### Option B: Citty (The Modern Choice)
Created by the UnJS team (Nuxt).
*   **Pros:** Built for TypeScript/ESM from day one. Extremely lightweight. Argument typing is inferred automatically.
*   **Cons:** Smaller ecosystem than Commander.
*   **Best For:** High-performance CLIs, monorepo tooling.

### Option C: Oclif (The Platform)
*   **Pros:** Built-in plugin system, auto-documentation, hooks, topic separation.
*   **Cons:** Heavy, strict directory structure, slower startup time.
*   **Best For:** Massive CLIs with 50+ commands or plugin marketplaces.

---

## 3. Interactive UX & DX

**@clack/prompts** has replaced **Inquirer** as the modern standard.
*   **Clack:** "Clean" UI, consistent styling, cancellation handling baked in.
*   **Inquirer:** Legacy, heavier, but has every possible prompt type.
*   **Ink:** Use ONLY if you need a full TUI (Terminal User Interface) with flexbox layouts (React for CLI). Overkill for linear wizards.

---

## 4. File System & Configuration

*   **File Ops:** Use `fs-extra` (legacy) or Node's native `fs/promises` + `globby` for patterns.
*   **Configuration:** `c12` (by UnJS) is superior to `cosmiconfig` in 2026.
    *   Loads `.config.ts`, `.json`, `.rc`.
    *   Supports "layers" (defaults -> user -> project -> env).

---

## 5. Testing Strategy

Do NOT use Jest (slow, bad ESM support). Use **Vitest**.

*   **Unit Tests:** Test command logic functions in isolation.
*   **Integration Tests:** Use `execa` to spawn your CLI binary against fixtures.

```typescript
// test/cli.test.ts
import { describe, it, expect } from 'vitest';
import { execa } from 'execa';

it('should print help', async () => {
  const { stdout } = await execa('node', ['./dist/cli.mjs', '--help']);
  expect(stdout).toContain('Usage: mekong [command]');
});
```

---

## 6. Code Examples

### A. Modern Setup (Commander + Clack)

```typescript
#!/usr/bin/env node
import { Command } from 'commander';
import { intro, text, outro, spinner } from '@clack/prompts';
import pc from 'picocolors';

const program = new Command();

program
  .name('mekong')
  .description('Mekong CLI tools')
  .version('1.0.0');

program.command('deploy')
  .description('Deploy services')
  .action(async () => {
    intro(pc.bgBlue(' MEKONG DEPLOY '));

    const env = await text({
      message: 'Target environment?',
      placeholder: 'production',
      initialValue: 'staging',
      validate(value) {
        if (value.length === 0) return 'Value is required!';
      },
    });

    const s = spinner();
    s.start('Deploying...');
    await new Promise(r => setTimeout(r, 1000)); // Fake work
    s.stop('Deployed!');

    outro('Success! 🚀');
  });

program.parse();
```

---

## 7. Integration Considerations

1.  **Monorepo:** If in a Turbo/Nx repo, ensure the CLI package builds to a standalone entry point.
2.  **Global vs Local:** Prefer `npx` execution (via `package.json` bin) over global installs.
3.  **Updates:** Implement an `update-notifier` check (or `update-check` package) to warn users of old versions.
4.  **Telemetry:** If needed, use strictly opt-in methods.

## 8. Final Recommendation for Mekong CLI

Given the `mekong-cli` context (likely a dev tool or platform interface):

*   **Framework:** **Commander.js** (Standardization)
*   **UX:** **@clack/prompts** (Polished feel)
*   **Build:** **Tsup** (Fastest TS -> JS bundle)
*   **Test:** **Vitest**

This stack minimizes maintenance overhead while providing a professional, "Silicon Valley" grade CLI experience.
