/**
 * Marketplace Installer — download, install, update SOP packages.
 * Installed packages available via `mekong sop list` and `mekong sop run`.
 * ROI: Engineering ROI — one-command SOP install for developer productivity.
 */
import { promises as fs } from 'fs';
import { join } from 'path';
import type { InstalledPackage, SopPackage } from './types.js';
import { ok, err } from '../types/common.js';
import type { Result } from '../types/common.js';
import { SopPackager } from './packager.js';
import { MarketplaceRegistry } from './registry.js';

export class MarketplaceInstaller {
  private readonly packager = new SopPackager();
  private readonly registry: MarketplaceRegistry;

  constructor(
    private readonly cacheDir: string,
    private readonly packagesDir: string,
    private readonly registryRepo: string,
  ) {
    this.registry = new MarketplaceRegistry(join(packagesDir, 'registry.json'));
  }

  /** Install a package from marketplace (local .mkg file) */
  async install(packageNameOrPath: string, _version?: string): Promise<Result<InstalledPackage>> {
    try {
      await this.registry.load();

      // Check if it's a local .mkg file path
      let mkgPath = packageNameOrPath;
      if (!packageNameOrPath.endsWith('.mkg')) {
        // Remote install: would download from registry — for now, error
        return err(new Error(
          `Remote install not yet supported. Use local .mkg file path.\n` +
          `Pack first: mekong marketplace pack <dir>`,
        ));
      }

      // Unpack to packages dir
      const content = await fs.readFile(mkgPath, 'utf-8');
      const data = JSON.parse(content) as { package: SopPackage };
      const pkg = data.package;
      const installPath = join(this.packagesDir, pkg.name.replace('/', '__'));

      // Check if already installed
      if (this.registry.has(pkg.name)) {
        const existing = this.registry.get(pkg.name)!;
        if (existing.package.version === pkg.version) {
          return err(new Error(`${pkg.name}@${pkg.version} already installed`));
        }
      }

      const unpackResult = await this.packager.unpack(mkgPath, installPath);
      if (!unpackResult.ok) return err(unpackResult.error);

      const installed: InstalledPackage = {
        package: pkg,
        installedAt: new Date().toISOString(),
        installPath,
        enabled: true,
        runCount: 0,
      };

      await this.registry.add(installed);
      return ok(installed);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Update installed package to latest */
  async update(packageName: string): Promise<Result<InstalledPackage>> {
    await this.registry.load();
    if (!this.registry.has(packageName)) {
      return err(new Error(`Package "${packageName}" not installed`));
    }
    // Remote update: would fetch latest from registry
    return err(new Error('Remote update not yet supported. Reinstall with new .mkg file.'));
  }

  /** Uninstall package */
  async uninstall(packageName: string): Promise<Result<void>> {
    try {
      await this.registry.load();
      const pkg = this.registry.get(packageName);
      if (!pkg) {
        return err(new Error(`Package "${packageName}" not installed`));
      }

      // Remove installed files
      await fs.rm(pkg.installPath, { recursive: true, force: true });
      await this.registry.remove(packageName);
      return ok(undefined);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** List installed packages */
  async listInstalled(): Promise<InstalledPackage[]> {
    await this.registry.load();
    return this.registry.list();
  }

  /** Check for available updates */
  async checkUpdates(): Promise<Array<{ package: string; current: string; latest: string }>> {
    // Will query registry for latest versions when remote support added
    void this.cacheDir;
    void this.registryRepo;
    return [];
  }
}
