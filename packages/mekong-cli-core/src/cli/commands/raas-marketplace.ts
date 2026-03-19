/**
 * raas-marketplace.ts — RaaS Marketplace + Analytics CLI commands
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';

export function registerRaasMarketplaceCommand(program: Command, _engine: MekongEngine): void {
  const mp = program
    .command('marketplace')
    .description('RaaS Marketplace — products, storefront, sales');

  mp
    .command('products')
    .description('List all products in catalog')
    .action(async () => {
      try {
        const { ProductCatalog } = await import('../../../../raas-marketplace/src/catalog.js');
        const catalog = new ProductCatalog();
        const products = catalog.listProducts();
        info(`── ${products.length} Products ──`);
        for (const p of products) {
          info(`  ${p.id}: ${p.name} — $${p.basePriceUsd}/mo [${p.tier}] ${p.active ? '✅' : '❌'}`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  mp
    .command('storefront')
    .description('Generate storefront JSON')
    .action(async () => {
      try {
        const { ProductCatalog } = await import('../../../../raas-marketplace/src/catalog.js');
        const { generateStorefrontJSON } = await import('../../../../raas-marketplace/src/storefront.js');
        const catalog = new ProductCatalog();
        const json = generateStorefrontJSON(catalog.listProducts());
        info(JSON.stringify(json, null, 2));
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  mp
    .command('qualify <name> <email> <company> <size> <budget>')
    .description('Qualify a lead and get tier recommendation')
    .action(async (name: string, email: string, company: string, size: string, budget: string) => {
      try {
        const { SalesBot } = await import('../../../../raas-marketplace/src/sales-bot.js');
        const bot = new SalesBot();
        const lead = { name, email, company, size: parseInt(size, 10), budget: parseInt(budget, 10), useCase: 'general' };
        const score = bot.qualifyLead(lead);
        info(`Lead Score: ${score.score}/100`);
        info(`Recommended Tier: ${score.tier}`);
        info(`Reasoning: ${score.reasoning}`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  // Analytics subcommand
  const analytics = program
    .command('sales-analytics')
    .description('RaaS sales analytics — funnel, MRR, churn');

  analytics
    .command('report')
    .description('Generate weekly sales report')
    .action(async () => {
      try {
        const { SalesAnalytics } = await import('../../../../raas-marketplace/src/analytics.js');
        const sa = new SalesAnalytics();
        const report = sa.generateWeeklySalesReport();
        info(report);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  analytics
    .command('funnel')
    .description('Show conversion funnel')
    .action(async () => {
      try {
        const { SalesAnalytics } = await import('../../../../raas-marketplace/src/analytics.js');
        const sa = new SalesAnalytics();
        const funnel = sa.getConversionFunnel();
        info('── Conversion Funnel ──');
        for (const step of funnel) {
          info(`  ${step.stage}: ${step.count} (${(step.conversionRate * 100).toFixed(1)}%)`);
        }
        info(`MRR: $${sa.getMRR()}`);
        info(`Churn: ${(sa.getChurnRate() * 100).toFixed(1)}%`);
        info(`LTV: $${sa.getLTV().toFixed(0)}`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
