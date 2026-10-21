/**
 * `mekong plugin` — Plugin management.
 *
 *   mekong plugin list                     List loaded plugins
 *   mekong plugin load <path>              Load a plugin
 *   mekong plugin unload <name>            Unload a plugin
 *   mekong plugin validate <path>          Validate plugin manifest
 *   mekong plugin create                   Interactive plugin scaffold
 *   mekong plugin permissions <name>       View plugin permissions
 */
import type { Command } from 'commander';
import { promises as fs } from 'fs';
import { join } from 'path';
import { PluginLoader } from '../../plugins/loader.js';
import type { PluginManifest } from '../../plugins/types.js';
import {
  PLUGIN_DIRS,
  buildNoopApi,
  runPluginCreate,
  runPluginPermissions,
} from './plugin-helpers.js';

export function registerPluginCommand(program: Command): void {
  const plugin = program
    .command('plugin')
    .description('Plugin management — load, unload, validate, and create plugins');

  plugin.command('list')
    .description('List loaded plugins')
    .action(async () => {
      const loader = new PluginLoader(PLUGIN_DIRS, buildNoopApi());
      const { loaded, failed } = await loader.loadAll();
      const plugins = loader.getPlugins();

      if (plugins.length === 0 && failed.length === 0) {
        console.log('No plugins found in:', PLUGIN_DIRS.join(', '));
        console.log('Use `mekong plugin load <path>` to load a plugin.');
        return;
      }

      if (plugins.length > 0) {
        console.log(`\nLoaded plugins (${loaded.length}):\n`);
        for (const p of plugins) {
          const provides = Object.entries(p.manifest.provides)
            .filter(([, v]) => Array.isArray(v) && v.length > 0)
            .map(([k, v]) => `${k}: ${(v as string[]).join(', ')}`)
            .join(' | ');
          console.log(`  ${p.manifest.name} v${p.manifest.version}`);
          console.log(`    ${p.manifest.description}`);
          if (provides) console.log(`    Provides: ${provides}`);
          console.log(`    Permissions: ${p.manifest.permissions.join(', ') || 'none'}`);
        }
      }

      if (failed.length > 0) {
        console.log(`\nFailed to load (${failed.length}):\n`);
        for (const f of failed) {
          console.log(`  ${f.name}: ${f.error}`);
        }
      }
    });

  plugin.command('load <path>')
    .description('Load a plugin from path (directory or manifest.json)')
    .action(async (pluginPath: string) => {
      const loader = new PluginLoader([], buildNoopApi());
      const manifestPath = pluginPath.endsWith('.json')
        ? pluginPath
        : join(pluginPath, 'plugin.json');

      const result = await loader.load(manifestPath);
      if (!result.ok) {
        console.error('Failed to load plugin:', result.error.message);
        process.exit(1);
      }
      const inst = result.value;
      console.log(`Loaded plugin: ${inst.manifest.name} v${inst.manifest.version}`);
      console.log(`Description: ${inst.manifest.description}`);
    });

  plugin.command('unload <name>')
    .description('Unload a plugin by name')
    .action(async (name: string) => {
      const loader = new PluginLoader(PLUGIN_DIRS, buildNoopApi());
      await loader.loadAll();
      const result = await loader.unload(name);
      if (!result.ok) {
        console.error('Failed to unload plugin:', result.error.message);
        process.exit(1);
      }
      console.log(`Unloaded plugin: ${name}`);
    });

  plugin.command('validate <path>')
    .description('Validate plugin manifest (plugin.json)')
    .action(async (pluginPath: string) => {
      const manifestPath = pluginPath.endsWith('.json')
        ? pluginPath
        : join(pluginPath, 'plugin.json');

      try {
        const raw = await fs.readFile(manifestPath, 'utf-8');
        const manifest = JSON.parse(raw) as PluginManifest;

        const errors: string[] = [];
        if (!manifest.name) errors.push('Missing: name');
        if (!manifest.version) errors.push('Missing: version');
        if (!manifest.description) errors.push('Missing: description');
        if (!manifest.author) errors.push('Missing: author');
        if (!manifest.mekongVersion) errors.push('Missing: mekongVersion');
        if (!manifest.main) errors.push('Missing: main');
        if (!Array.isArray(manifest.permissions)) errors.push('Missing: permissions (must be array)');

        if (errors.length > 0) {
          console.error('\nValidation failed:');
          errors.forEach(e => console.error(`  [ERROR] ${e}`));
          process.exit(1);
        }

        console.log(`Manifest valid: ${manifest.name} v${manifest.version}`);
        console.log(`Permissions: ${manifest.permissions.join(', ') || 'none'}`);
        const provides = Object.entries(manifest.provides)
          .filter(([, v]) => Array.isArray(v) && (v as string[]).length > 0)
          .map(([k, v]) => `${k}(${(v as string[]).length})`)
          .join(', ');
        if (provides) console.log(`Provides: ${provides}`);
      } catch (e) {
        console.error('Could not read manifest:', e instanceof Error ? e.message : String(e));
        process.exit(1);
      }
    });

  plugin.command('create')
    .description('Scaffold a new plugin directory')
    .option('--name <name>', 'Plugin name (e.g. my-plugin)')
    .option('--dir <dir>', 'Output directory', '.')
    .action(runPluginCreate);

  plugin.command('permissions <name>')
    .description('View permissions for a loaded plugin')
    .action(runPluginPermissions);
}
