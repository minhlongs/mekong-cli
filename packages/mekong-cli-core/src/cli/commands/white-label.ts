/**
 * white-label.ts — White-label configuration CLI commands
 * Brand config, custom domain, preview branded CLI output
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

interface BrandConfig {
  name: string;
  primary: string;
  logo: string;
  domain: string;
  tagline: string;
  supportEmail: string;
}

// In-memory config — production would persist to .mekong/whitelabel.json
let currentConfig: BrandConfig = {
  name: 'OpenClaw',
  primary: '#6366f1',
  logo: 'https://openclaw.io/logo.svg',
  domain: 'cli.openclaw.io',
  tagline: 'AI-operated business platform',
  supportEmail: 'support@openclaw.io',
};

function hexToAnsiApprox(hex: string): string {
  // Map hex color to nearest ANSI label for terminal preview
  const colorMap: Record<string, string> = {
    '#6366f1': 'indigo', '#3b82f6': 'blue', '#10b981': 'green',
    '#f59e0b': 'amber', '#ef4444': 'red', '#8b5cf6': 'violet',
    '#ec4899': 'pink', '#14b8a6': 'teal', '#f97316': 'orange',
  };
  return colorMap[hex.toLowerCase()] ?? hex;
}

export function registerWhiteLabelCommand(program: Command): void {
  const wl = program
    .command('whitelabel')
    .description('White-label configuration — branding, domain, preview');

  wl
    .command('config')
    .description('Show current white-label configuration')
    .action(() => {
      heading('White-Label Configuration');
      divider();
      keyValue('Brand name', currentConfig.name);
      keyValue('Primary color', `${currentConfig.primary} (${hexToAnsiApprox(currentConfig.primary)})`);
      keyValue('Logo URL', currentConfig.logo);
      keyValue('Custom domain', currentConfig.domain);
      keyValue('Tagline', currentConfig.tagline);
      keyValue('Support email', currentConfig.supportEmail);
      divider();
      info('Edit: mekong whitelabel brand --name <n> --primary <hex> --logo <url>');
      info('Domain: mekong whitelabel domain --custom <domain>');
      info('Preview: mekong whitelabel preview');
      info('');
    });

  wl
    .command('brand')
    .description('Set branding — name, primary color, logo URL')
    .option('--name <name>', 'Brand name')
    .option('--primary <color>', 'Primary hex color (e.g. #3b82f6)')
    .option('--logo <url>', 'Logo URL')
    .option('--tagline <text>', 'Brand tagline')
    .option('--support <email>', 'Support email')
    .action((opts: { name?: string; primary?: string; logo?: string; tagline?: string; support?: string }) => {
      heading('Update Brand Configuration');

      if (!opts.name && !opts.primary && !opts.logo && !opts.tagline && !opts.support) {
        warn('No options provided. Usage:');
        info('  mekong whitelabel brand --name "MyBrand" --primary "#3b82f6" --logo "https://..."');
        info('');
        return;
      }

      if (opts.name) { currentConfig.name = opts.name; success(`Brand name → ${opts.name}`); }
      if (opts.primary) {
        if (!/^#[0-9a-fA-F]{6}$/.test(opts.primary)) {
          warn(`Invalid hex color "${opts.primary}" — use format #rrggbb`);
        } else {
          currentConfig.primary = opts.primary;
          success(`Primary color → ${opts.primary} (${hexToAnsiApprox(opts.primary)})`);
        }
      }
      if (opts.logo) { currentConfig.logo = opts.logo; success(`Logo URL → ${opts.logo}`); }
      if (opts.tagline) { currentConfig.tagline = opts.tagline; success(`Tagline → ${opts.tagline}`); }
      if (opts.support) { currentConfig.supportEmail = opts.support; success(`Support email → ${opts.support}`); }

      divider();
      success('Brand configuration updated');
      info('Run `mekong whitelabel preview` to see how it looks');
      info('');
    });

  wl
    .command('domain')
    .description('Configure custom domain for white-label deployment')
    .option('--custom <domain>', 'Custom domain (e.g. cli.yourcompany.com)')
    .action((opts: { custom?: string }) => {
      heading('Custom Domain Configuration');

      if (!opts.custom) {
        keyValue('Current domain', currentConfig.domain);
        warn('Provide --custom to set a new domain');
        info('  mekong whitelabel domain --custom cli.yourcompany.com');
        info('');
        return;
      }

      const domain = opts.custom.replace(/^https?:\/\//, '');
      currentConfig.domain = domain;

      success(`Custom domain set: ${domain}`);
      divider();
      info('DNS Configuration Required:');
      info('');
      info(`  CNAME  ${domain}  →  raas.openclaw.io`);
      info('  TXT    _verify.' + domain + '  →  mekong-verify=<your-tenant-id>');
      info('');
      info('Steps:');
      info('  1. Add CNAME record in your DNS provider');
      info('  2. Add TXT verification record');
      info('  3. Wait for DNS propagation (5-60 min)');
      info('  4. SSL certificate auto-provisioned via Let\'s Encrypt');
      info('');
      info(`  Verify: curl -I https://${domain}/health`);
      info('');
    });

  wl
    .command('preview')
    .description('Preview branded CLI output sample')
    .action(() => {
      const brand = currentConfig;
      const color = hexToAnsiApprox(brand.primary);

      info('');
      info('┌─────────────────────────────────────────────────────────┐');
      info(`│  ${brand.name.padEnd(55)}│`);
      info(`│  ${brand.tagline.padEnd(55)}│`);
      info('└─────────────────────────────────────────────────────────┘');
      info('');
      heading(`${brand.name} CLI — Branded Preview`);
      info(`Primary color: ${brand.primary} (${color})`);
      info(`Domain: https://${brand.domain}`);
      divider();

      success(`Welcome to ${brand.name}!`);
      info('');
      info('Available commands:');
      info(`  ${brand.name.toLowerCase().replace(/\s/g, '-')} run       — Execute AI mission`);
      info(`  ${brand.name.toLowerCase().replace(/\s/g, '-')} status    — Check system status`);
      info(`  ${brand.name.toLowerCase().replace(/\s/g, '-')} billing   — View usage & billing`);
      info(`  ${brand.name.toLowerCase().replace(/\s/g, '-')} help      — Show all commands`);
      info('');
      info('Getting started:');
      info(`  1. Sign up at https://${brand.domain}`);
      info(`  2. Run: ${brand.name.toLowerCase().replace(/\s/g, '-')} onboard setup`);
      info(`  3. Questions? ${brand.supportEmail}`);
      divider();
      info(`Logo: ${brand.logo}`);
      info('');
      info('This is how your branded CLI will appear to end customers.');
      info('Customize further: mekong whitelabel brand --tagline "Your tagline"');
      info('');
    });
}
