// Sitemap generator — returns XML string
const BASE_URL = "https://agencyos.ai";

export async function generateDynamicSitemap(): Promise<string> {
  const urls = [{ loc: BASE_URL, lastmod: new Date().toISOString().split("T")[0] }];
  const entries = urls.map((u) => `<url><loc>${u.loc}</loc><lastmod>${u.lastmod}</lastmod></url>`).join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries}\n</urlset>`;
}
