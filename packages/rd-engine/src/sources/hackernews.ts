export interface HNStory {
  title: string;
  url: string;
  points: number;
  author: string;
  createdAt: string;
}

const HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search";

export async function fetchHNStories(query: string): Promise<HNStory[]> {
  try {
    const params = new URLSearchParams({
      query,
      tags: "story",
      hitsPerPage: "20",
    });

    const res = await fetch(`${HN_ALGOLIA_URL}?${params}`);

    if (!res.ok) {
      throw new Error(`HN Algolia error: ${res.status} ${res.statusText}`);
    }

    const data = (await res.json()) as {
      hits: Array<{
        title?: string;
        story_title?: string;
        url?: string;
        story_url?: string;
        points?: number;
        author?: string;
        created_at?: string;
      }>;
    };

    return data.hits
      .filter((hit) => (hit.title ?? hit.story_title) && (hit.url ?? hit.story_url))
      .map((hit) => ({
        title: hit.title ?? hit.story_title ?? "(no title)",
        url: hit.url ?? hit.story_url ?? "",
        points: hit.points ?? 0,
        author: hit.author ?? "unknown",
        createdAt: hit.created_at ?? new Date().toISOString(),
      }));
  } catch (err) {
    console.error(`[hackernews] Failed to fetch stories for "${query}":`, err);
    return [];
  }
}
