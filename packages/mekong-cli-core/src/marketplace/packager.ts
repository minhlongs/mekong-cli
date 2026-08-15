/**
 * SOP Package Builder — packs SOP + dependencies into .mkg (tar.gz) archive.
 * Structure: package.json, sop.yaml, agents/, tools/, templates/, README.md
 * ROI: Engineering ROI — enables SOP distribution and marketplace revenue.
 */
import { promises as fs } from 'fs';
import { join, relative } from 'path';
import { ok, err } from '../types/common.js';
import type { Result } from '../types/common.js';
import type { SopPackage } from './types.js';
import { SopPackageValidator } from './validator.js';

export class SopPackager {
  private readonly validator = new SopPackageValidator();

  /** Pack a directory into .mkg file (gzipped tar-like format using JSON manifest) */
  async pack(sourceDir: string, outputPath: string): Promise<Result<{ path: string; size: number }>> {
    // Validate first
    const validation = await this.validator.validateDir(sourceDir);
    if (!validation.ok) return err(validation.error);
    if (validation.value.errors.length > 0) {
      return err(new Error(`Validation failed:\n${validation.value.errors.join('\n')}`));
    }

    try {
      // Read package metadata
      const pkgJson = await fs.readFile(join(sourceDir, 'package.json'), 'utf-8');
      const pkg = JSON.parse(pkgJson) as SopPackage;

      // Collect all files
      const files = await this.collectFiles(sourceDir);
      const archive: Record<string, string> = {};

      for (const filePath of files) {
        const relPath = relative(sourceDir, filePath);
        const content = await fs.readFile(filePath, 'utf-8');
        archive[relPath] = content;
      }

      // Write as gzipped JSON (simple .mkg format)
      const manifest = JSON.stringify({ package: pkg, files: archive }, null, 2);
      const dir = outputPath.substring(0, outputPath.lastIndexOf('/'));
      await fs.mkdir(dir, { recursive: true });
      await fs.writeFile(outputPath, manifest, 'utf-8');

      const stat = await fs.stat(outputPath);
      return ok({ path: outputPath, size: stat.size });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Unpack .mkg file to directory */
  async unpack(mkgPath: string, targetDir: string): Promise<Result<SopPackage>> {
    try {
      const content = await fs.readFile(mkgPath, 'utf-8');
      const data = JSON.parse(content) as { package: SopPackage; files: Record<string, string> };

      await fs.mkdir(targetDir, { recursive: true });

      for (const [relPath, fileContent] of Object.entries(data.files)) {
        const fullPath = join(targetDir, relPath);
        const dir = fullPath.substring(0, fullPath.lastIndexOf('/'));
        await fs.mkdir(dir, { recursive: true });
        await fs.writeFile(fullPath, fileContent, 'utf-8');
      }

      return ok(data.package);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Validate a package directory before packing */
  async validate(sourceDir: string): Promise<Result<{ warnings: string[]; errors: string[] }>> {
    return this.validator.validateDir(sourceDir);
  }

  /** Recursively collect packable files */
  private async collectFiles(dir: string): Promise<string[]> {
    const results: string[] = [];
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
      const full = join(dir, entry.name);
      if (entry.isDirectory()) {
        results.push(...await this.collectFiles(full));
      } else {
        results.push(full);
      }
    }
    return results;
  }
}
