export const meta = {
  name: 'agent-architecture-audit',
  description: 'Audit agents, tools, loops, and commands in the Mekong harness',
  phases: [
    { title: 'Inventory', detail: 'Map all agents, tools, loops, commands' },
    { title: 'Analyze', detail: 'Evaluate coupling, coverage, gaps, MCP validity' },
    { title: 'Report', detail: 'Consolidated architecture report' },
  ],
};

// Phase 1: Inventory
const inventory = await agent(
  'Inventory the Mekong CLI harness at /Users/macbook/mekong-cli/harness. Read these EXACT files: (1) src/core/types.ts or src/core/types.js for agent/tool/loop interface definitions, (2) src/providers/llm-router.ts or .js for routing config, (3) agents/ directory (all .md files) for agent definitions, (4) tools/ directory (all .ts/.js files) for tool implementations, (5) commands/ directory (all .ts/.js) for command handlers, (6) loops/ directory (all .ts/.js) for loop definitions. For each category list: every found item, its file path, its declared capabilities or signature, and whether it is referenced by any other component. Flag anything that is defined but never invoked.',
  {
    label: 'inventory-all',
    phase: 'Inventory',
    effort: 'high',
  },
);

log('Inventory complete. Analyzing architecture...');

// Phase 2: Analyze
const analysis = await agent(
  `Based on this inventory, produce a structured analysis covering ONLY these checks: (A) tool coverage gaps per agent, (B) Binh Pháp coupling violations (tools/loops/commands making out-of-scope edits outside their declared role), (C) MCP service validity (whether externally referenced services actually exist or are stubs), (D) dependency risks in tool-loop command chaining (what breaks if one layer changes), (E) security exposure surface (what sensitive paths each component can touch). Be evidence-first: cite file paths and line references.`,
  {
    label: 'architecture-analysis',
    phase: 'Analyze',
    effort: 'high',
  },
);

log('Analysis complete. Generating report...');

// Phase 3: Report
const report = await agent(
  `Write a comprehensive Vietnamese Binh Pháp architecture audit report with these sections: (1) Tổng quan hệ thống (system map), (2) Bản đổ công cụ & vòng lặp (tool/loop inventory table), (3) Kết quả kiểm tra (findings for each check A-E with severity), (4) Rủi ro & khuyến nghị (risks prioritized, remediation order), (5) Hành động tiếp theo (concrete next steps). Include file citations. Tone: strategist to general, not developer to developer.`,
  {
    label: 'final-report',
    phase: 'Report',
    effort: 'xhigh',
  },
);

return report;
