import type { RdItem } from "./analyzer.js";

function estimateEffort(score: number): string {
  if (score >= 80) return "Low (1-2 days) — high alignment, likely drop-in";
  if (score >= 50) return "Medium (3-5 days) — moderate adaptation needed";
  return "High (1-2 weeks) — significant integration work required";
}

function inferIntegrationSteps(item: RdItem): string[] {
  const steps: string[] = [];

  if (item.source === "github") {
    steps.push(`Clone or install: \`npm install ${item.name}\` or submodule`);
    steps.push("Review API surface and adapt to OpenClaw agent interface");
    steps.push("Add to `packages/` or reference from `mekong/adapters/`");
  } else if (item.source === "npm") {
    steps.push(`Install: \`npm install ${item.name}\``);
    steps.push("Import and wrap in an OpenClaw skill or adapter module");
    steps.push("Add to relevant `@openclaw/*` package dependencies");
  } else {
    steps.push("Read linked article or repo for implementation patterns");
    steps.push("Extract relevant techniques and document in `.claude/skills/`");
    steps.push("Create prototype if applicable");
  }

  steps.push("Write integration test covering primary use case");
  return steps;
}

export function generateProposal(item: RdItem): string {
  const effort = estimateEffort(item.score);
  const steps = inferIntegrationSteps(item);
  const date = new Date().toISOString().split("T")[0];

  return [
    `## ${item.name}`,
    "",
    `> **Source:** ${item.source} | **Relevance Score:** ${item.score}/100 | **Date:** ${date}`,
    "",
    "### Why",
    "",
    item.description || "No description available.",
    "",
    `Relevance score of **${item.score}** indicates strong keyword alignment with OpenClaw's`,
    "core stack (claude, vibe-coding, ai-agent, mcp, coding-cli).",
    "",
    "### How to Integrate",
    "",
    ...steps.map((s) => `- ${s}`),
    "",
    "### Effort Estimate",
    "",
    effort,
    "",
    `### Reference`,
    "",
    `- ${item.url}`,
  ].join("\n");
}
