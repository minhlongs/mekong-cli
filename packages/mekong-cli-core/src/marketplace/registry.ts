/**
 * Local SOP/plugin registry — tracks installed marketplace packages.
 * Storage: ~/.mekong/marketplace/registry.json
 * ROI: Engineering ROI — local package management for developer workflow.
 */
import { promises as fs } from 'fs';
import { dirname } from 'path';
import type { InstalledPackage } from './types.js';
import { ok, err } from '../types/common.js';
import type { Result } from '../types/common.js';

export class MarketplaceRegistry {
  private packages = new Map<string, InstalledPackage>();

  constructor(private readonly registryPath: string) {}

  /** Load registry from disk */
  async load(): Promise<void> {
    try {
      const content = await fs.readFile(this.registryPath, 'utf-8');
      const data = JSON.parse(content) as InstalledPackage[];
      this.packages.clear();
      for (const pkg of data) {
        this.packages.set(pkg.package.name, pkg);
      }
    } catch {
      // File doesn't exist yet — start empty
      this.packages.clear();
    }
  }

  /** Save registry to disk */
  async save(): Promise<void> {
    const dir = dirname(this.registryPath);
    await fs.mkdir(dir, { recursive: true });
    const data = Array.from(this.packages.values());
    await fs.writeFile(this.registryPath, JSON.stringify(data, null, 2), 'utf-8');
  }

  /** Add installed package to registry */
  async add(pkg: InstalledPackage): Promise<Result<void>> {
    this.packages.set(pkg.package.name, pkg);
    await this.save();
    return ok(undefined);
  }

  /** Remove package from registry */
  async remove(packageName: string): Promise<Result<void>> {
    if (!this.packages.has(packageName)) {
      return err(new Error(`Package "${packageName}" not found in registry`));
    }
    this.packages.delete(packageName);
    await this.save();
    return ok(undefined);
  }

  /** Get installed package by name */
  get(packageName: string): InstalledPackage | undefined {
    return this.packages.get(packageName);
  }

  /** List all installed packages */
  list(): InstalledPackage[] {
    return Array.from(this.packages.values());
  }

  /** Check if package is installed */
  has(packageName: string): boolean {
    return this.packages.has(packageName);
  }

  /** Increment run count for a package */
  async recordRun(packageName: string): Promise<void> {
    const pkg = this.packages.get(packageName);
    if (pkg) {
      pkg.runCount += 1;
      pkg.lastRun = new Date().toISOString();
      await this.save();
    }
  }
}
