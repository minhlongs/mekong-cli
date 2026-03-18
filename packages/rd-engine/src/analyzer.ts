const RELEVANCE_KEYWORDS = [
  "openclaw",
  "claude",
  "gemini",
  "vibe-coding",
  "ai-agent",
  "mcp",
  "coding-cli",
];

export interface RdItem {
  source: "github" | "npm" | "hackernews";
  name: string;
  description: string;
  url: string;
  score: number;
}

export function scoreRelevance(item: Omit<RdItem, "score">): number {
  const text = `${item.name} ${item.description}`.toLowerCase();
  let score = 0;

  for (const keyword of RELEVANCE_KEYWORDS) {
    if (text.includes(keyword.toLowerCase())) {
      // Exact name match is worth more
      score += item.name.toLowerCase().includes(keyword.toLowerCase()) ? 20 : 10;
    }
  }

  // Cap at 100
  return Math.min(score, 100);
}

export function filterHighRelevance(items: RdItem[], threshold = 20): RdItem[] {
  return items.filter((item) => item.score >= threshold);
}
