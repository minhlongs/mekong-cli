/**
 * marketplace-helpers.ts — Factory builders and pack/validate/publish handlers for marketplace CLI.
 */
import { MarketplaceDiscovery } from '../../marketplace/discovery.js';
import { MarketplaceInstaller } from '../../marketplace/installer.js';
import { SopPackager } from '../../marketplace/packager.js';
import { homedir } from 'os';
import { join } from 'path';

export const REGISTRY_REPO = 'mekong-cli/marketplace';
export const CACHE_DIR = join(homedir(), '.mekong', 'marketplace', 'cache');
export const PACKAGES_DIR = join(homedir(), '.mekong', 'marketplace', 'packages');

export function buildDiscovery(): MarketplaceDiscovery {
  return new MarketplaceDiscovery(REGISTRY_REPO, CACHE_DIR);
}

export function buildInstaller(): MarketplaceInstaller {
  return new MarketplaceInstaller(CACHE_DIR, PACKAGES_DIR, REGISTRY_REPO);
}

export async function runMarketplacePack(dir: string, opts: { out?: string }): Promise<void> {
  const packager = new SopPackager();
  const outPath = opts.out ?? `${dir.replace(/\/$/, '')}.mkg`;
  console.log(`Packing ${dir} → ${outPath}...`);
  const result = await packager.pack(dir, outPath);
  if (!result.ok) {
    console.error('Pack failed:', result.error.message);
    process.exit(1);
  }
  console.log(`Packed: ${result.value.path} (${(result.value.size / 1024).toFixed(1)} KB)`);
}

export async function runMarketplaceValidate(dir: string): Promise<void> {
  const packager = new SopPackager();
  const result = await packager.validate(dir);
  if (!result.ok) {
    console.error('Validation error:', result.error.message);
    process.exit(1);
  }
  const { warnings, errors } = result.value;
  if (errors.length > 0) {
    console.error('\nErrors:');
    errors.forEach(e => console.error(`  [ERROR] ${e}`));
  }
  if (warnings.length > 0) {
    console.warn('\nWarnings:');
    warnings.forEach(w => console.warn(`  [WARN ] ${w}`));
  }
  if (errors.length === 0) {
    console.log(`\nValidation passed${warnings.length > 0 ? ` with ${warnings.length} warning(s)` : ''}.`);
  } else {
    console.error(`\nValidation failed: ${errors.length} error(s).`);
    process.exit(1);
  }
}

export async function runMarketplacePublish(mkg: string): Promise<void> {
  console.log(`Publishing ${mkg}...`);
  console.log('Note: Publishing requires a GitHub token and marketplace registry access.');
  console.log('See: https://github.com/mekong-cli/marketplace for setup instructions.');
}
