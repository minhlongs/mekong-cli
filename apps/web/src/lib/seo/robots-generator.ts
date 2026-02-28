// robots.txt generator
export function generateRobotsTxt(sitemapUrl: string) {
  return `User-agent: *\nAllow: /\nSitemap: ${sitemapUrl}`;
}

export function generateRobots() {
  return generateRobotsTxt("https://agencyos.ai/sitemap.xml");
}
