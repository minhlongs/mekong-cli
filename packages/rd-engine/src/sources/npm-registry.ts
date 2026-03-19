export interface NpmPackage {
  name: string;
  description: string;
  version: string;
  weeklyDownloads: number;
  url: string;
}

const SEARCH_QUERIES = ["claude-code", "ai-agent-cli", "coding-assistant"];
const NPM_SEARCH_URL = "https://registry.npmjs.org/-/v1/search";
const NPM_DOWNLOADS_URL = "https://api.npmjs.org/downloads/point/last-week";

async function fetchWeeklyDownloads(packageName: string): Promise<number> {
  try {
    const res = await fetch(`${NPM_DOWNLOADS_URL}/${encodeURIComponent(packageName)}`);
    if (!res.ok) return 0;
    const data = (await res.json()) as { downloads?: number };
    return data.downloads ?? 0;
  } catch {
    return 0;
  }
}

async function searchPackages(query: string): Promise<NpmPackage[]> {
  const params = new URLSearchParams({ text: query, size: "10" });
  const res = await fetch(`${NPM_SEARCH_URL}?${params}`);

  if (!res.ok) {
    throw new Error(`npm registry error: ${res.status} ${res.statusText}`);
  }

  const data = (await res.json()) as {
    objects: Array<{
      package: {
        name: string;
        description?: string;
        version: string;
        links: { npm?: string };
      };
    }>;
  };

  const packages = await Promise.all(
    data.objects.map(async ({ package: pkg }) => {
      const weeklyDownloads = await fetchWeeklyDownloads(pkg.name);
      return {
        name: pkg.name,
        description: pkg.description ?? "",
        version: pkg.version,
        weeklyDownloads,
        url: pkg.links.npm ?? `https://www.npmjs.com/package/${pkg.name}`,
      };
    })
  );

  return packages;
}

export async function searchNpmPackages(query: string): Promise<NpmPackage[]>;
export async function searchNpmPackages(): Promise<NpmPackage[]>;
export async function searchNpmPackages(query?: string): Promise<NpmPackage[]> {
  const queries = query ? [query] : SEARCH_QUERIES;
  const results: NpmPackage[] = [];
  const seen = new Set<string>();

  for (const q of queries) {
    try {
      const packages = await searchPackages(q);
      for (const pkg of packages) {
        if (!seen.has(pkg.name)) {
          seen.add(pkg.name);
          results.push(pkg);
        }
      }
    } catch (err) {
      console.error(`[npm-registry] Failed to fetch query "${q}":`, err);
    }
  }

  return results.sort((a, b) => b.weeklyDownloads - a.weeklyDownloads);
}
