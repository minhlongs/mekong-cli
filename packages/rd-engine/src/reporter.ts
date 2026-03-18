import type { RdItem } from "./analyzer.js";
import { generateProposal } from "./proposer.js";

function groupBySource(items: RdItem[]): Record<string, RdItem[]> {
  return items.reduce<Record<string, RdItem[]>>((acc, item) => {
    const group = acc[item.source] ?? [];
    group.push(item);
    acc[item.source] = group;
    return acc;
  }, {});
}

function sourceHeading(source: string): string {
  const labels: Record<string, string> = {
    github: "GitHub Trending",
    npm: "npm Registry",
    hackernews: "Hacker News",
  };
  return labels[source] ?? source;
}

function renderItemRow(item: RdItem): string {
  const desc = item.description.length > 80
    ? item.description.slice(0, 77) + "..."
    : item.description;
  return `| [${item.name}](${item.url}) | ${item.score} | ${desc} |`;
}

export function generateWeeklyReport(items: RdItem[]): string {
  const date = new Date().toISOString().split("T")[0];
  const grouped = groupBySource(items);
  const topItems = [...items].sort((a, b) => b.score - a.score).slice(0, 5);

  const sections: string[] = [
    `# R&D Weekly Report`,
    "",
    `**Date:** ${date}  `,
    `**Total items scanned:** ${items.length}  `,
    `**High-relevance items:** ${items.filter((i) => i.score >= 20).length}`,
    "",
    "---",
    "",
    "## Top Recommendations",
    "",
    "| Name | Score | Description |",
    "|------|-------|-------------|",
    ...topItems.map(renderItemRow),
    "",
    "---",
    "",
  ];

  for (const [source, sourceItems] of Object.entries(grouped)) {
    sections.push(`## ${sourceHeading(source)}`);
    sections.push("");
    sections.push("| Name | Score | Description |");
    sections.push("|------|-------|-------------|");
    for (const item of sourceItems) {
      sections.push(renderItemRow(item));
    }
    sections.push("");
    sections.push("---");
    sections.push("");
  }

  if (topItems.length > 0) {
    sections.push("## Integration Proposals");
    sections.push("");
    for (const item of topItems) {
      sections.push(generateProposal(item));
      sections.push("");
    }
  }

  return sections.join("\n");
}
