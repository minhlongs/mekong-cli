/**
 * rd.ts — R&D engine CLI commands
 * Scan global vibe-coding community, generate reports.
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';

export function registerRdCommand(program: Command, _engine: MekongEngine): void {
  const rd = program
    .command('rd')
    .description('R&D engine — scan vibe-coding community for tools & trends');

  rd
    .command('scan')
    .description('Manual R&D scan across GitHub, npm, HackerNews')
    .action(async () => {
      try {
        const { fetchTrendingRepos } = await import('@openclaw/rd-engine/sources/github-trending');
        const { searchNpmPackages } = await import('@openclaw/rd-engine/sources/npm-registry');
        const { fetchHNStories } = await import('@openclaw/rd-engine/sources/hackernews');
        const { scoreRelevance, filterHighRelevance } = await import('@openclaw/rd-engine/analyzer');

        info('Scanning GitHub trending...');
        const repos = await fetchTrendingRepos('vibe-coding');
        info(`  Found ${repos.length} repos`);

        info('Scanning npm registry...');
        const pkgs = await searchNpmPackages('ai-agent-cli');
        info(`  Found ${pkgs.length} packages`);

        info('Scanning HackerNews...');
        const stories = await fetchHNStories('vibe coding AI');
        info(`  Found ${stories.length} stories`);

        // Score and filter
        const allItems = [
          ...repos.map(r => ({ source: 'github' as const, name: r.name, description: r.description || '', url: r.url, score: 0 })),
          ...pkgs.map(p => ({ source: 'npm' as const, name: p.name, description: p.description || '', url: p.url, score: 0 })),
          ...stories.map(s => ({ source: 'hackernews' as const, name: s.title, description: s.title, url: s.url || '', score: 0 })),
        ].map(item => ({ ...item, score: scoreRelevance(item) }));

        const relevant = filterHighRelevance(allItems, 30);
        info(`\n── Top ${relevant.length} Relevant Items ──`);
        for (const item of relevant.slice(0, 10)) {
          info(`  [${item.score}] ${item.source}: ${item.name}`);
        }

        success(`Scan complete: ${allItems.length} total, ${relevant.length} relevant`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  rd
    .command('report')
    .description('Generate weekly R&D report')
    .action(async () => {
      try {
        const { fetchTrendingRepos } = await import('@openclaw/rd-engine/sources/github-trending');
        const { searchNpmPackages } = await import('@openclaw/rd-engine/sources/npm-registry');
        const { scoreRelevance } = await import('@openclaw/rd-engine/analyzer');
        const { generateWeeklyReport } = await import('@openclaw/rd-engine/reporter');
        const fs = await import('fs');
        const path = await import('path');

        info('Generating R&D report...');
        const repos = await fetchTrendingRepos('vibe-coding');
        const pkgs = await searchNpmPackages('claude-code');

        const items = [
          ...repos.map(r => ({ source: 'github' as const, name: r.name, description: r.description || '', url: r.url, score: 0 })),
          ...pkgs.map(p => ({ source: 'npm' as const, name: p.name, description: p.description || '', url: p.url, score: 0 })),
        ].map(item => ({ ...item, score: scoreRelevance(item) }));

        const report = generateWeeklyReport(items);
        const reportsDir = path.resolve('plans/reports');
        if (!fs.existsSync(reportsDir)) fs.mkdirSync(reportsDir, { recursive: true });
        const date = new Date().toISOString().split('T')[0];
        const reportPath = path.join(reportsDir, `rd-weekly-${date}.md`);
        fs.writeFileSync(reportPath, report);

        success(`Report saved: ${reportPath}`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
