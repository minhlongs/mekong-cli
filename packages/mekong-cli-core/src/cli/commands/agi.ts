/**
 * agi.ts — AGI Self-Evolution CLI commands
 * Status metrics and self-improvement triggers.
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';

export function registerAgiCommand(program: Command, _engine: MekongEngine): void {
  const agi = program
    .command('agi')
    .description('AGI self-evolution engine — metrics, evolve, benchmark');

  agi
    .command('status')
    .description('Show evolution metrics: quality score, capabilities, lessons learned')
    .action(async () => {
      try {
        const { analyzeCodebase, getQualityScore } = await import('../../../../agi-evolution/src/self-improver.js');
        const { checkVersions } = await import('../../../../agi-evolution/src/version-tracker.js');

        info('── AGI Evolution Status ──');

        // Codebase quality
        const analysis = analyzeCodebase(process.cwd());
        const score = getQualityScore(analysis);
        info(`Quality Score: ${score}/100`);
        info(`Files: ${analysis.totalFiles} | Lines: ${analysis.totalLines}`);
        info(`Anti-patterns: ${analysis.oversizedFiles} oversized, ${analysis.anyTypes} any-types, ${analysis.todoCount} TODOs`);

        // Version report
        info('\n── Dependency Versions ──');
        const versions = checkVersions();
        for (const v of versions) {
          info(`  ${v.name}: ${v.currentVersion || 'not found'}`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  agi
    .command('evolve')
    .description('Trigger self-improvement cycle: analyze → propose → report')
    .action(async () => {
      try {
        const { analyzeCodebase, generateRefactoringProposals, getQualityScore } = await import('../../../../agi-evolution/src/self-improver.js');

        info('Running self-improvement cycle...');
        const analysis = analyzeCodebase(process.cwd());
        const score = getQualityScore(analysis);
        const proposals = generateRefactoringProposals(analysis);

        info(`Quality Score: ${score}/100`);
        info(`Found ${proposals.length} improvement proposals:`);
        for (const p of proposals.slice(0, 10)) {
          info(`  [${p.priority}] ${p.file}: ${p.issue} → ${p.suggestion}`);
        }

        if (proposals.length === 0) {
          success('No improvements needed — codebase is clean!');
        } else {
          success(`${proposals.length} proposals generated. Review and apply as needed.`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  agi
    .command('benchmark')
    .description('Show competitive benchmark report')
    .action(async () => {
      try {
        const { BenchmarkRunner } = await import('../../../../agi-evolution/src/benchmark.js');
        const runner = new BenchmarkRunner();
        const report = runner.generateCompetitiveReport();
        info(report || 'No benchmarks recorded yet. Use the API to record benchmarks first.');
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
