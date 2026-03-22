/**
 * `mekong gtm` — Go-To-Market automation subcommands.
 *
 *   mekong gtm producthunt   ProductHunt launch checklist & automation
 *   mekong gtm appsumo       AppSumo LTD deal setup & tracking
 *   mekong gtm social        Social media campaign management
 *   mekong gtm schedule      Launch timeline & milestone tracker
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

// Today: 2026-03-22
const TODAY = new Date('2026-03-22');

function daysFromNow(days: number): string {
  const d = new Date(TODAY);
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0] as string;
}

/** DRY helper — renders engine health footer */
function showEngineHealth(engine?: MekongEngine, label = 'Engine Status'): void {
  try {
    const health = engine?.openclaw?.getHealth();
    if (!health) return;
    divider();
    info(label);
    keyValue('  Uptime', `${Math.round(health.uptime / 1000)}s`);
    keyValue('  Missions completed', `${health.missionsCompleted}`);
    keyValue('  AGI score', `${health.agiScore}/100`);
    keyValue('  Circuit breaker', health.circuitBreakerState);
  } catch { /* engine not ready */ }
}

export function registerGtmCommand(program: Command, engine?: MekongEngine): void {
  const cmd = program.command('gtm').description('Go-to-market automation');

  // --- producthunt ---
  cmd.command('producthunt')
    .description('ProductHunt launch checklist & automation')
    .action(() => {
      heading('ProductHunt Launch');
      info(`Launch date: ${daysFromNow(7)}`);
      divider();

      const checklist = [
        { label: 'Create maker profile',          status: 'done' },
        { label: 'Upload product screenshots',    status: 'done' },
        { label: 'Write tagline (60 chars max)',  status: 'done' },
        { label: 'Prepare hunter outreach',       status: 'pending' },
        { label: 'Schedule launch post',          status: 'pending' },
        { label: 'Email list pre-warm (500+)',    status: 'blocked' },
        { label: 'Slack community notification', status: 'pending' },
        { label: 'First comment template ready', status: 'done' },
      ];

      heading('Checklist');
      for (const item of checklist) {
        const icon = item.status === 'done' ? '✓' : item.status === 'blocked' ? '✗' : '○';
        console.log(`  ${icon} [${item.status.padEnd(7)}] ${item.label}`);
      }
      divider();

      heading('Targets');
      keyValue('Upvote goal (day 1)',  '500');
      keyValue('Comments target',     '50');
      keyValue('Launch window',       '12:01 AM PST');
      keyValue('Estimated ranking',   'Top 5 of the day');

      success('Launch checklist loaded');

      // Engine health as platform readiness section
      showEngineHealth(engine, 'Platform Readiness');
    });

  // --- appsumo ---
  cmd.command('appsumo')
    .description('AppSumo LTD deal setup & tracking')
    .action(() => {
      heading('AppSumo LTD Deal');
      divider();

      const tiers = [
        { name: 'Tier 1', price: '$49',  features: '200 MCU/mo, 2 seats',         codes: 312, redeemed: 189 },
        { name: 'Tier 2', price: '$99',  features: '1,000 MCU/mo, 5 seats',        codes: 248, redeemed: 134 },
        { name: 'Tier 3', price: '$199', features: 'Unlimited MCU, 15 seats + API', codes: 95,  redeemed: 41  },
      ];

      heading('Deal Tiers');
      for (const t of tiers) {
        keyValue(t.name, `${t.price} — ${t.features}`);
        keyValue('  Codes', `${t.redeemed}/${t.codes} redeemed`);
      }
      divider();

      heading('Deal Metrics');
      const totalRevenue = (189 * 49) + (134 * 99) + (41 * 199);
      keyValue('Total revenue', `$${totalRevenue.toLocaleString()}`);
      keyValue('Refund rate',   '2.1%');
      keyValue('Deal status',   'Active — 14 days remaining');
      keyValue('Avg rating',    '4.8 / 5 (87 reviews)');

      success('AppSumo deal metrics loaded');

      // Fire-and-forget deal optimization analysis
      void engine?.openclaw?.submitMission({
        goal: `Analyze AppSumo LTD deal performance: $${totalRevenue.toLocaleString()} revenue, 2.1% refund rate, 4.8/5 rating`,
        complexity: 'standard',
      });
    });

  // --- social ---
  cmd.command('social')
    .description('Social media campaign management')
    .action(() => {
      heading('Social Media Campaign');
      divider();

      const platforms = [
        { name: 'Twitter/X',   posts: 12, engagement: '3.2%', reach: '24.5K', status: 'active'    },
        { name: 'LinkedIn',    posts: 6,  engagement: '5.8%', reach: '8.1K',  status: 'active'    },
        { name: 'Reddit',      posts: 3,  engagement: '8.4%', reach: '15.2K', status: 'pending'   },
        { name: 'HackerNews',  posts: 1,  engagement: '12%',  reach: '40K',   status: 'scheduled' },
      ];

      heading('Platform Performance');
      for (const p of platforms) {
        keyValue(p.name.padEnd(12), `${p.status} | ${p.posts} posts | ${p.engagement} eng | ${p.reach} reach`);
      }
      divider();

      // AI content complexity estimation
      try {
        const contentSummary = platforms.map(p => `${p.name}: ${p.posts} posts`).join(', ');
        const complexity = engine?.openclaw?.classifyComplexity(contentSummary);
        if (complexity) keyValue('Content complexity', complexity);
      } catch { /* engine not ready */ }

      heading('Post Templates');
      info('Twitter: "We just launched Mekong CLI — AI that runs your company. 🚀 #ProductHunt #AI"');
      info('LinkedIn: "Excited to announce... [long form post]"');
      info('Reddit: "Show HN: Mekong CLI — open source AI business OS"');

      success('Social campaign data loaded');
    });

  // --- schedule ---
  cmd.command('schedule')
    .description('Launch timeline & milestone tracker')
    .action(() => {
      heading('Launch Schedule');
      divider();

      const milestones = [
        { date: daysFromNow(-7), label: 'Beta closed',         status: 'done',    owner: 'CTO'       },
        { date: daysFromNow(-3), label: 'Docs published',      status: 'done',    owner: 'Marketing' },
        { date: daysFromNow(0),  label: 'Pre-launch email',    status: 'today',   owner: 'Marketing' },
        { date: daysFromNow(3),  label: 'PH hunter outreach',  status: 'pending', owner: 'Founder'   },
        { date: daysFromNow(7),  label: 'ProductHunt launch',  status: 'pending', owner: 'Founder'   },
        { date: daysFromNow(10), label: 'AppSumo deal live',   status: 'pending', owner: 'Sales'     },
        { date: daysFromNow(14), label: 'Post-launch review',  status: 'pending', owner: 'CTO'       },
        { date: daysFromNow(21), label: 'Revenue milestone',   status: 'pending', owner: 'Finance'   },
      ];

      for (const m of milestones) {
        const icon = m.status === 'done' ? '✓' : m.status === 'today' ? '→' : '○';
        if (m.status === 'today') warn(`  ${icon} ${m.date}  ${m.label.padEnd(24)} [${m.owner}]`);
        else console.log(`  ${icon} ${m.date}  ${m.label.padEnd(24)} [${m.owner}]`);
      }
      divider();

      const done = milestones.filter(m => m.status === 'done').length;
      keyValue('Progress', `${done}/${milestones.length} milestones complete`);
      success('Launch schedule loaded');

      // Engine status alongside schedule
      showEngineHealth(engine, 'Engine Status');
    });
}
