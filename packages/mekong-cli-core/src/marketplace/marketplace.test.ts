/**
 * Marketplace module tests — validator, registry, packager, discovery, installer
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { promises as fs } from 'fs';
import { join } from 'path';
import { SopPackageValidator } from './validator.js';
import { MarketplaceRegistry } from './registry.js';
import { SopPackager } from './packager.js';
import { MarketplaceDiscovery } from './discovery.js';
import { MarketplaceInstaller } from './installer.js';
import { MarketplacePublisher } from './publisher.js';
import type { InstalledPackage, MarketplaceListing } from './types.js';

const TEST_DIR = '/tmp/mekong-marketplace-test';
const TEST_PKG_DIR = join(TEST_DIR, 'test-pkg');

const VALID_PKG_JSON = {
  name: '@test/my-sop',
  version: '1.0.0',
  description: 'A test SOP package',
  author: { name: 'Test Author' },
  license: 'MIT',
  category: 'devops',
  tags: ['test', 'ci'],
  mekongVersion: '0.3.0',
  dependencies: {},
  files: ['sop.yaml'],
  pricing: { type: 'free' },
};

const VALID_SOP_YAML = `sop:
  name: "Test SOP"
  version: "1.0.0"
  steps:
    - id: step1
      name: "Test step"
      action: shell
      command: "echo hello"
`;

async function setupTestPkg(): Promise<void> {
  await fs.mkdir(TEST_PKG_DIR, { recursive: true });
  await fs.writeFile(join(TEST_PKG_DIR, 'package.json'), JSON.stringify(VALID_PKG_JSON, null, 2));
  await fs.writeFile(join(TEST_PKG_DIR, 'sop.yaml'), VALID_SOP_YAML);
  await fs.writeFile(join(TEST_PKG_DIR, 'README.md'), '# Test SOP\nA test package.');
}

async function cleanup(): Promise<void> {
  await fs.rm(TEST_DIR, { recursive: true, force: true });
}

// ── SopPackageValidator ─────────────────────────────────────────────────────

describe('SopPackageValidator', () => {
  const validator = new SopPackageValidator();

  beforeEach(setupTestPkg);
  afterEach(cleanup);

  it('validates valid package directory', async () => {
    const result = await validator.validateDir(TEST_PKG_DIR);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.errors).toHaveLength(0);
    }
  });

  it('errors on missing package.json', async () => {
    await fs.unlink(join(TEST_PKG_DIR, 'package.json'));
    const result = await validator.validateDir(TEST_PKG_DIR);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.errors.length).toBeGreaterThan(0);
    }
  });

  it('errors on missing sop.yaml', async () => {
    await fs.unlink(join(TEST_PKG_DIR, 'sop.yaml'));
    const result = await validator.validateDir(TEST_PKG_DIR);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.errors.some(e => e.includes('sop.yaml'))).toBe(true);
    }
  });

  it('warns on missing README', async () => {
    await fs.unlink(join(TEST_PKG_DIR, 'README.md'));
    const result = await validator.validateDir(TEST_PKG_DIR);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.warnings.some(w => w.includes('README'))).toBe(true);
    }
  });

  it('validates correct metadata', () => {
    const result = validator.validateMetadata(VALID_PKG_JSON);
    expect(result.ok).toBe(true);
  });

  it('rejects unscoped name', () => {
    const result = validator.validateMetadata({ ...VALID_PKG_JSON, name: 'no-scope' });
    expect(result.ok).toBe(false);
  });

  it('rejects invalid version', () => {
    const result = validator.validateMetadata({ ...VALID_PKG_JSON, version: 'abc' });
    expect(result.ok).toBe(false);
  });

  it('rejects missing required fields', () => {
    const result = validator.validateMetadata({ name: '@test/pkg' });
    expect(result.ok).toBe(false);
  });

  it('rejects non-object input', () => {
    const result = validator.validateMetadata(null);
    expect(result.ok).toBe(false);
  });

  it('scanForSecrets returns array', () => {
    const result = validator.scanForSecrets('/some/path');
    expect(Array.isArray(result)).toBe(true);
  });

  it('checkAbsolutePaths returns array', () => {
    const result = validator.checkAbsolutePaths('/some/path');
    expect(Array.isArray(result)).toBe(true);
  });
});

// ── MarketplaceRegistry ─────────────────────────────────────────────────────

describe('MarketplaceRegistry', () => {
  const registryPath = join(TEST_DIR, 'registry.json');
  let registry: MarketplaceRegistry;

  beforeEach(async () => {
    await fs.mkdir(TEST_DIR, { recursive: true });
    registry = new MarketplaceRegistry(registryPath);
  });
  afterEach(cleanup);

  const makePkg = (name: string): InstalledPackage => ({
    package: { ...VALID_PKG_JSON, name } as InstalledPackage['package'],
    installedAt: new Date().toISOString(),
    installPath: `/tmp/pkg/${name}`,
    enabled: true,
    runCount: 0,
  });

  it('starts empty', async () => {
    await registry.load();
    expect(registry.list()).toHaveLength(0);
  });

  it('adds and retrieves package', async () => {
    await registry.load();
    const pkg = makePkg('@test/sop-a');
    await registry.add(pkg);
    expect(registry.has('@test/sop-a')).toBe(true);
    expect(registry.get('@test/sop-a')?.package.name).toBe('@test/sop-a');
  });

  it('persists to disk and reloads', async () => {
    await registry.load();
    await registry.add(makePkg('@test/persist'));

    const registry2 = new MarketplaceRegistry(registryPath);
    await registry2.load();
    expect(registry2.has('@test/persist')).toBe(true);
  });

  it('removes package', async () => {
    await registry.load();
    await registry.add(makePkg('@test/removable'));
    const result = await registry.remove('@test/removable');
    expect(result.ok).toBe(true);
    expect(registry.has('@test/removable')).toBe(false);
  });

  it('remove returns error for unknown package', async () => {
    await registry.load();
    const result = await registry.remove('@test/nonexistent');
    expect(result.ok).toBe(false);
  });

  it('records run count', async () => {
    await registry.load();
    await registry.add(makePkg('@test/counted'));
    await registry.recordRun('@test/counted');
    await registry.recordRun('@test/counted');
    expect(registry.get('@test/counted')?.runCount).toBe(2);
    expect(registry.get('@test/counted')?.lastRun).toBeDefined();
  });
});

// ── SopPackager ─────────────────────────────────────────────────────────────

describe('SopPackager', () => {
  const packager = new SopPackager();
  const outputPath = join(TEST_DIR, 'output', 'test.mkg');

  beforeEach(setupTestPkg);
  afterEach(cleanup);

  it('packs valid directory into .mkg', async () => {
    const result = await packager.pack(TEST_PKG_DIR, outputPath);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.size).toBeGreaterThan(0);
      expect(result.value.path).toBe(outputPath);
    }
  });

  it('unpacks .mkg back to directory', async () => {
    const packResult = await packager.pack(TEST_PKG_DIR, outputPath);
    expect(packResult.ok).toBe(true);

    const unpackDir = join(TEST_DIR, 'unpacked');
    const unpackResult = await packager.unpack(outputPath, unpackDir);
    expect(unpackResult.ok).toBe(true);
    if (unpackResult.ok) {
      expect(unpackResult.value.name).toBe('@test/my-sop');
    }
  });

  it('roundtrip preserves sop.yaml content', async () => {
    await packager.pack(TEST_PKG_DIR, outputPath);
    const unpackDir = join(TEST_DIR, 'roundtrip');
    await packager.unpack(outputPath, unpackDir);
    const yaml = await fs.readFile(join(unpackDir, 'sop.yaml'), 'utf-8');
    expect(yaml).toContain('Test SOP');
  });

  it('validate returns validation result', async () => {
    const result = await packager.validate(TEST_PKG_DIR);
    expect(result.ok).toBe(true);
  });

  it('pack fails on invalid directory', async () => {
    await fs.unlink(join(TEST_PKG_DIR, 'sop.yaml'));
    const result = await packager.pack(TEST_PKG_DIR, outputPath);
    expect(result.ok).toBe(false);
  });

  it('unpack fails on non-existent file', async () => {
    const result = await packager.unpack('/tmp/nonexistent.mkg', join(TEST_DIR, 'bad'));
    expect(result.ok).toBe(false);
  });
});

// ── MarketplaceDiscovery ────────────────────────────────────────────────────

describe('MarketplaceDiscovery', () => {
  const cacheDir = join(TEST_DIR, 'cache');
  let discovery: MarketplaceDiscovery;

  const listings: MarketplaceListing[] = [
    {
      package: { ...VALID_PKG_JSON, name: '@acme/deploy-sop', category: 'devops', tags: ['deploy', 'ci'] } as MarketplaceListing['package'],
      stats: { downloads: 100, stars: 20, lastUpdated: '2026-03-01T00:00:00Z', reviews: 5, avgRating: 4.5 },
      verified: true, featured: true,
    },
    {
      package: { ...VALID_PKG_JSON, name: '@acme/marketing-sop', category: 'marketing', tags: ['seo'] } as MarketplaceListing['package'],
      stats: { downloads: 50, stars: 10, lastUpdated: '2026-02-15T00:00:00Z', reviews: 3, avgRating: 4.0 },
      verified: false, featured: false,
    },
  ];

  beforeEach(async () => {
    await fs.mkdir(cacheDir, { recursive: true });
    await fs.writeFile(join(cacheDir, 'index.json'), JSON.stringify(listings));
    discovery = new MarketplaceDiscovery('mekong-cli/marketplace', cacheDir);
  });
  afterEach(cleanup);

  it('search returns all when no filter', async () => {
    const result = await discovery.search({});
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value).toHaveLength(2);
  });

  it('search filters by text query', async () => {
    const result = await discovery.search({ query: 'deploy' });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value).toHaveLength(1);
      expect(result.value[0]!.package.name).toBe('@acme/deploy-sop');
    }
  });

  it('search filters by category', async () => {
    const result = await discovery.search({ category: 'marketing' });
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value).toHaveLength(1);
  });

  it('search filters by tags', async () => {
    const result = await discovery.search({ tags: ['seo'] });
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value).toHaveLength(1);
  });

  it('search sorts by stars', async () => {
    const result = await discovery.search({ sortBy: 'stars' });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value[0]!.package.name).toBe('@acme/deploy-sop');
    }
  });

  it('search paginates', async () => {
    const result = await discovery.search({ limit: 1, offset: 1 });
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value).toHaveLength(1);
  });

  it('getPackageInfo returns found package', async () => {
    const result = await discovery.getPackageInfo('@acme/deploy-sop');
    expect(result.ok).toBe(true);
  });

  it('getPackageInfo errors on unknown', async () => {
    const result = await discovery.getPackageInfo('@acme/nonexistent');
    expect(result.ok).toBe(false);
  });

  it('getFeatured returns only featured', async () => {
    const result = await discovery.getFeatured();
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value).toHaveLength(1);
      expect(result.value[0]!.featured).toBe(true);
    }
  });

  it('getCategories returns known list', async () => {
    const cats = await discovery.getCategories();
    expect(cats).toContain('devops');
    expect(cats).toContain('marketing');
    expect(cats.length).toBeGreaterThan(5);
  });
});

// ── MarketplaceInstaller ────────────────────────────────────────────────────

describe('MarketplaceInstaller', () => {
  const cacheDir = join(TEST_DIR, 'inst-cache');
  const pkgsDir = join(TEST_DIR, 'inst-pkgs');
  let installer: MarketplaceInstaller;

  beforeEach(async () => {
    await setupTestPkg();
    await fs.mkdir(cacheDir, { recursive: true });
    await fs.mkdir(pkgsDir, { recursive: true });
    installer = new MarketplaceInstaller(cacheDir, pkgsDir, 'mekong-cli/marketplace');
  });
  afterEach(cleanup);

  it('installs from local .mkg file', async () => {
    const packager = new SopPackager();
    const mkgPath = join(TEST_DIR, 'installable.mkg');
    await packager.pack(TEST_PKG_DIR, mkgPath);

    const result = await installer.install(mkgPath);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.package.name).toBe('@test/my-sop');
      expect(result.value.enabled).toBe(true);
    }
  });

  it('listInstalled returns installed packages', async () => {
    const packager = new SopPackager();
    const mkgPath = join(TEST_DIR, 'list-test.mkg');
    await packager.pack(TEST_PKG_DIR, mkgPath);
    await installer.install(mkgPath);

    const list = await installer.listInstalled();
    expect(list).toHaveLength(1);
  });

  it('uninstalls package', async () => {
    const packager = new SopPackager();
    const mkgPath = join(TEST_DIR, 'uninstall-test.mkg');
    await packager.pack(TEST_PKG_DIR, mkgPath);
    await installer.install(mkgPath);

    const result = await installer.uninstall('@test/my-sop');
    expect(result.ok).toBe(true);

    const list = await installer.listInstalled();
    expect(list).toHaveLength(0);
  });

  it('errors on non-mkg path without remote support', async () => {
    const result = await installer.install('@remote/pkg');
    expect(result.ok).toBe(false);
  });

  it('errors on duplicate install', async () => {
    const packager = new SopPackager();
    const mkgPath = join(TEST_DIR, 'dup-test.mkg');
    await packager.pack(TEST_PKG_DIR, mkgPath);
    await installer.install(mkgPath);

    const result = await installer.install(mkgPath);
    expect(result.ok).toBe(false);
  });

  it('checkUpdates returns empty array', async () => {
    const updates = await installer.checkUpdates();
    expect(updates).toHaveLength(0);
  });

  it('uninstall errors on unknown package', async () => {
    const result = await installer.uninstall('@test/nonexistent');
    expect(result.ok).toBe(false);
  });
});

// ── MarketplacePublisher ────────────────────────────────────────────────────

describe('MarketplacePublisher', () => {
  it('publish errors without GitHub token', async () => {
    const publisher = new MarketplacePublisher({ registryRepo: 'test/repo' });
    const result = await publisher.publish('/tmp/test.mkg');
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error.message).toContain('GitHub token');
  });

  it('unpublish errors without GitHub token', async () => {
    const publisher = new MarketplacePublisher({ registryRepo: 'test/repo' });
    const result = await publisher.unpublish('@test/pkg', '1.0.0');
    expect(result.ok).toBe(false);
  });
});
