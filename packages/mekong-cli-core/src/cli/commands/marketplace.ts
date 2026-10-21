/**
 * `mekong marketplace` — SOP marketplace.
 *
 *   mekong marketplace search <query>      Search SOPs
 *   mekong marketplace browse [--cat=X]    Browse by category
 *   mekong marketplace info <package>      Package details
 *   mekong marketplace install <package>   Install SOP package
 *   mekong marketplace update [package]    Update installed packages
 *   mekong marketplace uninstall <pkg>     Remove package
 *   mekong marketplace list               List installed packages
 *   mekong marketplace pack <dir>          Pack SOP for publishing
 *   mekong marketplace validate <dir>      Validate package
 *   mekong marketplace publish <mkg>       Publish to marketplace
 */
import type { Command } from 'commander';
import {
  buildDiscovery,
  buildInstaller,
  runMarketplacePack,
  runMarketplaceValidate,
  runMarketplacePublish,
} from './marketplace-helpers.js';

export function registerMarketplaceCommand(program: Command): void {
  const mp = program
    .command('marketplace')
    .description('SOP marketplace — browse, install, and publish SOP packages');

  mp.command('search <query>')
    .description('Search marketplace SOPs')
    .option('--cat <category>', 'Filter by category')
    .option('--limit <n>', 'Max results', '20')
    .action(async (query: string, opts: { cat?: string; limit: string }) => {
      const discovery = buildDiscovery();
      const result = await discovery.search({
        query,
        category: opts.cat,
        limit: parseInt(opts.limit, 10) || 20,
      });
      if (!result.ok) {
        console.error('Search failed:', result.error.message);
        process.exit(1);
      }
      const listings = result.value;
      if (listings.length === 0) {
        console.log(`No packages found for "${query}".`);
        return;
      }
      console.log(`\nFound ${listings.length} packages:\n`);
      for (const l of listings) {
        const price = l.package.pricing.type === 'free' ? 'FREE'
          : l.package.pricing.price != null ? `$${l.package.pricing.price}` : l.package.pricing.type;
        console.log(`  ${l.package.name}@${l.package.version} [${price}]`);
        console.log(`    ${l.package.description}`);
        console.log(`    Downloads: ${l.stats.downloads}  Stars: ${l.stats.stars}  Rating: ${l.stats.avgRating.toFixed(1)}`);
      }
    });

  mp.command('browse')
    .description('Browse SOPs by category')
    .option('--cat <category>', 'Category filter')
    .action(async (opts: { cat?: string }) => {
      const discovery = buildDiscovery();
      if (!opts.cat) {
        const cats = await discovery.getCategories();
        console.log('\nAvailable categories:\n');
        cats.forEach(c => console.log(`  - ${c}`));
        console.log('\nUse --cat <category> to browse a specific category.');
        return;
      }
      const result = await discovery.search({ category: opts.cat, limit: 20 });
      if (!result.ok) {
        console.error('Browse failed:', result.error.message);
        process.exit(1);
      }
      const listings = result.value;
      console.log(`\nCategory: ${opts.cat} (${listings.length} packages)\n`);
      for (const l of listings) {
        console.log(`  ${l.package.name}@${l.package.version} — ${l.package.description}`);
      }
    });

  mp.command('info <package>')
    .description('Show package details')
    .action(async (pkg: string) => {
      const discovery = buildDiscovery();
      const result = await discovery.getPackageInfo(pkg);
      if (!result.ok) {
        console.error('Package not found:', result.error.message);
        process.exit(1);
      }
      const l = result.value;
      const p = l.package;
      console.log(`\n${p.name} v${p.version}`);
      console.log(`Description: ${p.description}`);
      console.log(`Author: ${p.author.name}${p.author.email ? ` <${p.author.email}>` : ''}`);
      console.log(`Category: ${p.category}  License: ${p.license}`);
      console.log(`Tags: ${p.tags.join(', ')}`);
      console.log(`Pricing: ${p.pricing.type}${p.pricing.price != null ? ` ($${p.pricing.price})` : ''}`);
      console.log(`Stats: ${l.stats.downloads} downloads, ${l.stats.stars} stars, ${l.stats.avgRating.toFixed(1)} rating`);
      if (p.homepage) console.log(`Homepage: ${p.homepage}`);
    });

  mp.command('install <package>')
    .description('Install a SOP package (.mkg file or package name)')
    .option('--version <ver>', 'Specific version')
    .action(async (pkg: string, opts: { version?: string }) => {
      console.log(`Installing ${pkg}...`);
      const installer = buildInstaller();
      const result = await installer.install(pkg, opts.version);
      if (!result.ok) {
        console.error('Install failed:', result.error.message);
        process.exit(1);
      }
      const installed = result.value;
      console.log(`Installed ${installed.package.name}@${installed.package.version} to ${installed.installPath}`);
    });

  mp.command('update [package]')
    .description('Update installed packages (all if no arg)')
    .action(async (pkg?: string) => {
      const installer = buildInstaller();
      if (pkg) {
        const result = await installer.update(pkg);
        if (!result.ok) {
          console.error('Update failed:', result.error.message);
          process.exit(1);
        }
        console.log(`Updated ${pkg} to v${result.value.package.version}`);
      } else {
        const updates = await installer.checkUpdates();
        if (updates.length === 0) {
          console.log('All packages are up to date.');
          return;
        }
        console.log(`\nAvailable updates (${updates.length}):\n`);
        for (const u of updates) {
          console.log(`  ${u.package}: ${u.current} → ${u.latest}`);
        }
      }
    });

  mp.command('uninstall <package>')
    .description('Uninstall a SOP package')
    .action(async (pkg: string) => {
      const installer = buildInstaller();
      const result = await installer.uninstall(pkg);
      if (!result.ok) {
        console.error('Uninstall failed:', result.error.message);
        process.exit(1);
      }
      console.log(`Uninstalled ${pkg}`);
    });

  mp.command('list')
    .description('List installed packages')
    .action(async () => {
      const installer = buildInstaller();
      const packages = await installer.listInstalled();
      if (packages.length === 0) {
        console.log('No packages installed. Use `mekong marketplace search` to find SOPs.');
        return;
      }
      console.log(`\nInstalled packages (${packages.length}):\n`);
      for (const p of packages) {
        const status = p.enabled ? 'enabled' : 'disabled';
        console.log(`  ${p.package.name}@${p.package.version} [${status}] — ${p.runCount} runs`);
        if (p.lastRun) console.log(`    Last run: ${p.lastRun.slice(0, 10)}`);
      }
    });

  mp.command('pack <dir>')
    .description('Pack SOP directory into .mkg archive')
    .option('--out <path>', 'Output path')
    .action(runMarketplacePack);

  mp.command('validate <dir>')
    .description('Validate package before publishing')
    .action(runMarketplaceValidate);

  mp.command('publish <mkg>')
    .description('Publish .mkg package to marketplace')
    .action(runMarketplacePublish);
}
