/**
 * vc-governance.ts — VC governance CLI commands
 * Pitch, data room, compliance, exit strategy.
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';

export function registerVcGovernanceCommand(program: Command, _engine: MekongEngine): void {
  const vc = program
    .command('vc')
    .description('VC-ready governance — pitch, data room, compliance, exit');

  vc
    .command('pitch')
    .description('Generate pitch deck data from current KPIs')
    .action(async () => {
      try {
        const { PitchGenerator } = await import('../../../../vc-governance/src/pitch-generator.js');
        const gen = new PitchGenerator();
        const data = gen.generatePitchData({
          name: 'OpenClaw', stage: 'seed', mrr: 0, users: 0,
          market: 'AI Developer Tools', founded: '2025',
        });
        info('── Pitch Deck Data ──');
        info(`Problem: ${data.problem}`);
        info(`Solution: ${data.solution}`);
        info(`Market: TAM $${(data.market.tam / 1e9).toFixed(1)}B, SAM $${(data.market.sam / 1e6).toFixed(0)}M, SOM $${(data.market.som / 1e6).toFixed(0)}M`);
        info(`One-liner: ${gen.generateOneLiner()}`);
        success('Pitch data generated. Use --json for export.');
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  vc
    .command('dataroom')
    .description('Show data room status')
    .action(async () => {
      try {
        const { DataRoom } = await import('../../../../vc-governance/src/data-room.js');
        const room = new DataRoom();
        const docs = room.listDocuments();
        info(`── Data Room: ${docs.length} documents ──`);
        for (const d of docs) {
          info(`  [${d.category}] ${d.name}`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  vc
    .command('compliance')
    .description('Run compliance audit (ISO 27001, SOC 2, GDPR)')
    .action(async () => {
      try {
        const { ComplianceEngine } = await import('../../../../vc-governance/src/iso-compliance.js');
        const engine = new ComplianceEngine();
        const iso27001 = engine.auditISO27001();
        const soc2 = engine.auditSOC2();
        const gdpr = engine.checkGDPR();
        info('── Compliance Audit ──');
        info(`ISO 27001: ${iso27001.score}/${iso27001.maxScore}`);
        info(`SOC 2: ${soc2.score}/${soc2.maxScore}`);
        info(`GDPR: ${gdpr.filter(c => c.status === 'pass').length}/${gdpr.length} pass`);
        const report = engine.generateComplianceReport();
        info(report);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  vc
    .command('exit')
    .description('Calculate exit valuation and strategy')
    .action(async () => {
      try {
        const { ExitEngine } = await import('../../../../vc-governance/src/exit-engine.js');
        const engine = new ExitEngine();
        const val = engine.calculateValuation('revenue-multiple', {
          annualRevenue: 600000, growthRate: 2.0, ebitdaMargin: 0.3, discountRate: 0.15,
        });
        const strategy = engine.recommendStrategy({
          name: 'OpenClaw', stage: 'seed', mrr: 50000, users: 500,
          market: 'AI Developer Tools', founded: '2025',
        });
        info('── Exit Analysis ──');
        info(`Valuation (revenue multiple): $${(val / 1e6).toFixed(1)}M`);
        info(`Recommended: ${strategy.type} (${(strategy.probability * 100).toFixed(0)}% probability)`);
        info(`Timeline: ${strategy.timeline}`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
