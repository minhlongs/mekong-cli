export const meta = {
  name: 'mekong-architecture-audit',
  description: 'Full architecture audit of mekong-cli: agents, tools, loops, commands, MCP validity',
  phases: [
    { title: 'Inventory', detail: 'Map all agents, tools, loops, commands, MCP services' },
    { title: 'Analyze', detail: 'Coupling, coverage, gaps, validity, security' },
    { title: 'Report', detail: 'Structured findings with severity and remediation' },
  ],
};

// Phase 1: Inventory
const inventory = await agent(
  'Inventory the Mekong CLI at /Users/macbook/mekong-cli. Read these EXACT files: (1) CLAUDE.md for architecture overview, (2) src/core/ for MCU billing, orchestrator, LLM routing, (3) src/commands/ for all command modules, (4) src/api/ for REST routes, (5) src/middleware/ for license gate, (6) src/services/ for external clients. For each category list: every found item, its file path, its declared capabilities, and whether referenced by others. Flag orphaned/orphan definitions.',
  { label: 'inventory-mekong', phase: 'Inventory', effort: 'high' }
);

log('Inventory complete. Analyzing...');

// Phase 2: Analyze
const analysis = await agent(
  `Based on this inventory, produce a structured analysis: (A) tool/command coverage gaps per layer, (B) coupling violations between seed/tree/forest/land, (C) MCP/service validity (are referenced services real or stubs?), (D) dependency risks in command→API→service chains, (E) security exposure (what sensitive paths can each component touch? license gate bypass risks?). Cite file paths and line refs.`,
  { label: 'mekong-analysis', phase: 'Analyze', effort: 'high' }
);

log('Analysis complete. Generating report...');

// Phase 3: Report
const report = await agent(
  `Write a bilingual (Vietnamese primary, English secondary) architecture audit report with these sections: (1) Tổng quan hệ thống (system map with 4-layer diagram), (2) Bản đổ công cụ & lệnh (inventory table), (3) Kết quả kiểm tra (findings A-E with severity: CRITICAL/HIGH/MEDIUM/LOW), (4) Rủi ro & khuyến nghị (prioritized risks + remediation), (5) Hành động tiếp theo (concrete next steps). Tone: strategist to general.`,
  { label: 'mekong-final-report', phase: 'Report', effort: 'xhigh' }
);

return report;
