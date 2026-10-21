/**
 * plugin-helpers.ts — Plugin directory config, no-op API builder, and scaffold/permission handlers.
 */
import { promises as fs } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import { PluginLoader } from '../../plugins/loader.js';
import { createPluginApi } from '../../plugins/api.js';
import type { PluginManifest } from '../../plugins/types.js';

export const PLUGIN_DIRS = [
  join(homedir(), '.mekong', 'plugins'),
  join(process.cwd(), 'mekong-plugins'),
];

/** Minimal no-op API for CLI context (no live engine deps needed) */
export function buildNoopApi() {
  return createPluginApi('cli', [], {
    toolRegistry: { register: () => undefined },
    agentPool: { registerDefinition: () => undefined },
    config: {},
    memory: { get: async () => undefined, set: async () => undefined },
    eventBus: { emit: () => undefined, on: () => undefined },
    llmRouter: { chat: async () => ({ content: '' }) },
    logger: {
      debug: (m: string) => console.debug(m),
      info: (m: string) => console.info(m),
      warn: (m: string) => console.warn(m),
      error: (m: string) => console.error(m),
    },
  });
}

export async function runPluginCreate(opts: { name?: string; dir: string }): Promise<void> {
  const name = opts.name ?? 'my-plugin';
  const outDir = join(opts.dir, name);

  const manifest: PluginManifest = {
    name,
    version: '0.1.0',
    description: `${name} — Mekong CLI plugin`,
    author: 'your-name',
    mekongVersion: '0.3.0',
    provides: { tools: [], agents: [], hooks: [] },
    requires: {},
    main: 'index.js',
    permissions: [],
  };

  const indexJs = `/**
 * ${name} plugin entry point.
 * Export a 'hooks' object implementing PluginHooks.
 */
export const hooks = {
  async onLoad() {
    console.log('[${name}] Plugin loaded');
  },
  async onUnload() {
    console.log('[${name}] Plugin unloaded');
  },
};
`;

  try {
    await fs.mkdir(outDir, { recursive: true });
    await fs.writeFile(join(outDir, 'plugin.json'), JSON.stringify(manifest, null, 2), 'utf-8');
    await fs.writeFile(join(outDir, 'index.js'), indexJs, 'utf-8');
    await fs.writeFile(join(outDir, 'README.md'), `# ${name}\n\nA Mekong CLI plugin.\n`, 'utf-8');

    console.log(`\nPlugin scaffolded at: ${outDir}`);
    console.log('Files created:');
    console.log('  plugin.json  — manifest');
    console.log('  index.js     — entry point');
    console.log('  README.md    — documentation');
    console.log(`\nNext: mekong plugin validate ${outDir}`);
    console.log(`      mekong plugin load ${outDir}`);
  } catch (e) {
    console.error('Failed to scaffold plugin:', e instanceof Error ? e.message : String(e));
    process.exit(1);
  }
}

export async function runPluginPermissions(name: string): Promise<void> {
  const loader = new PluginLoader(PLUGIN_DIRS, buildNoopApi());
  await loader.loadAll();
  const plugins = loader.getPlugins();
  const inst = plugins.find(p => p.manifest.name === name);
  if (!inst) {
    console.error(`Plugin "${name}" not found. Run \`mekong plugin list\` to see loaded plugins.`);
    process.exit(1);
  }
  console.log(`\nPermissions for ${inst.manifest.name} v${inst.manifest.version}:\n`);
  if (inst.manifest.permissions.length === 0) {
    console.log('  (no permissions declared)');
  } else {
    inst.manifest.permissions.forEach(p => console.log(`  - ${p}`));
  }
}
