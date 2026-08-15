export const meta = {
  name: 'mekong-arch-bug-audit',
  description: 'Binh Pháp architecture audit: agents, tools, loops, commands, MCP validity',
  phases: [
    { title: 'Inventory', detail: 'Map agents, tools, loops, commands, MCP services' },
    { title: 'Analyze', detail: 'Coupling, coverage, MCP validity, security exposure' },
    { title: 'Report', detail: 'Structured findings with severity ranked by risk' },
  ],
};

const ROOT = '/Users/macbook/mekong-cli';

// Phase 1: Full inventory
const inventory = await agent(
  `Inventory the Mekong CLI at ${ROOT}. Read CLAUDE.md for architecture overview, then src/core/ (MCU billing, orchestrator, LLM routing), src/commands/ (command modules), src/api/ (REST routes), src/middleware/ (license gate), src/services/ (Polar, org). For each: file path, capabilities, who references it. Flag orphaned items. Keep it concise — bullet lists only.`,
  { label: 'inv-mekong', phase: 'Inventory', effort: 'high', model: 'sonnet' }
);

log('Inventory complete. Running deep analysis...');

// Phase 2: Deep analysis
const analysis = await agent(
  `From the inventory above, analyze: (A) tool/command coverage gaps per layer, (B) coupling violations between seed/tree/forest/land layers, (C) MCP/service validity — are referenced services real or stubs?, (D) dependency risks in command→API→service chains, (E) security exposure — what sensitive paths can each component touch? Any license gate bypass risks? Cite file paths and line references.`,
  { label: 'analyze-mekong', phase: 'Analyze', effort: 'high', model: 'sonnet' }
);

log('Analysis complete. Generating final report...');

// Phase 3: Binh Pháp report
const report = await agent(
  `Write a Vietnamese Binh Pháp (Sun Tzu Art of War) architecture audit report: (1) Tổng quan hệ thống — 4-layer diagram (seed/tree/forest/land) with 4 funnels (Zalo, Tax, Accounting, AI Video), (2) Bản đổ công cụ & lệnh — table of all agents, tools, loops, commands with file paths and status, (3) Kết quả kiểm tra — findings for checks A-E with severity (CRITICAL/HIGH/MEDIUM/LOW) and file:line evidence, (4) Rủi ro & khuyến nghị — prioritized risks + concrete remediation steps, (5) Hành động tiếp theo — ranked next steps.`,
  { label: 'report-mekong', phase: 'Report', effort: 'xhigh', model: 'sonnet' }
);

return report;
