export interface TrendingRepo {
  name: string;
  fullName: string;
  description: string;
  stars: number;
  url: string;
  language: string;
  topics: string[];
}

const SEARCH_QUERIES = ["vibe-coding", "ai-cli", "claude-code", "coding-agent"];
const GITHUB_SEARCH_URL = "https://api.github.com/search/repositories";

async function searchRepos(query: string): Promise<TrendingRepo[]> {
  const params = new URLSearchParams({
    q: query,
    sort: "stars",
    order: "desc",
    per_page: "10",
  });

  const res = await fetch(`${GITHUB_SEARCH_URL}?${params}`, {
    headers: { Accept: "application/vnd.github.v3+json" },
  });

  if (!res.ok) {
    throw new Error(`GitHub API error: ${res.status} ${res.statusText}`);
  }

  const data = (await res.json()) as {
    items: Array<{
      name: string;
      full_name: string;
      description: string | null;
      stargazers_count: number;
      html_url: string;
      language: string | null;
      topics: string[];
    }>;
  };

  return data.items.map((item) => ({
    name: item.name,
    fullName: item.full_name,
    description: item.description ?? "",
    stars: item.stargazers_count,
    url: item.html_url,
    language: item.language ?? "unknown",
    topics: item.topics ?? [],
  }));
}

export async function fetchTrendingRepos(topic?: string): Promise<TrendingRepo[]> {
  const queries = topic ? [topic] : SEARCH_QUERIES;
  const results: TrendingRepo[] = [];
  const seen = new Set<string>();

  for (const query of queries) {
    try {
      const repos = await searchRepos(query);
      for (const repo of repos) {
        if (!seen.has(repo.fullName)) {
          seen.add(repo.fullName);
          results.push(repo);
        }
      }
    } catch (err) {
      console.error(`[github-trending] Failed to fetch query "${query}":`, err);
    }
  }

  return results.sort((a, b) => b.stars - a.stars);
}
