/**
 * Marketplace Discovery — search, browse, and explore SOPs.
 * Sources: GitHub registry index.json, local cache.
 * ROI: Operational ROI — users discover and purchase SOPs via marketplace.
 */
import { promises as fs } from 'fs';
import { join } from 'path';
import type { MarketplaceListing, MarketplaceSearchQuery } from './types.js';
import { ok, err } from '../types/common.js';
import type { Result } from '../types/common.js';

const CATEGORIES = [
  'devops', 'development', 'business', 'finance',
  'marketing', 'sales', 'support', 'analytics', 'automation', 'other',
];

export class MarketplaceDiscovery {
  private index: MarketplaceListing[] = [];

  constructor(
    private readonly registryRepo: string,
    private readonly cacheDir: string,
  ) {}

  /** Search marketplace using local cached index */
  async search(query: MarketplaceSearchQuery): Promise<Result<MarketplaceListing[]>> {
    await this.loadIndex();
    let results = [...this.index];

    // Filter by text query
    if (query.query) {
      const q = query.query.toLowerCase();
      results = results.filter(l =>
        l.package.name.toLowerCase().includes(q) ||
        l.package.description.toLowerCase().includes(q) ||
        l.package.tags.some(t => t.toLowerCase().includes(q)),
      );
    }

    // Filter by category
    if (query.category) {
      results = results.filter(l => l.package.category === query.category);
    }

    // Filter by tags
    if (query.tags && query.tags.length > 0) {
      results = results.filter(l =>
        query.tags!.some(t => l.package.tags.includes(t)),
      );
    }

    // Filter by pricing
    if (query.pricing && query.pricing !== 'all') {
      results = results.filter(l => l.package.pricing.type === query.pricing);
    }

    // Sort
    const sortBy = query.sortBy ?? 'downloads';
    results.sort((a, b) => {
      switch (sortBy) {
        case 'downloads': return b.stats.downloads - a.stats.downloads;
        case 'stars': return b.stats.stars - a.stats.stars;
        case 'rating': return b.stats.avgRating - a.stats.avgRating;
        case 'recent': return new Date(b.stats.lastUpdated).getTime() - new Date(a.stats.lastUpdated).getTime();
        default: return 0;
      }
    });

    // Pagination
    const offset = query.offset ?? 0;
    const limit = query.limit ?? 20;
    return ok(results.slice(offset, offset + limit));
  }

  /** Get package details */
  async getPackageInfo(packageName: string): Promise<Result<MarketplaceListing>> {
    await this.loadIndex();
    const found = this.index.find(l => l.package.name === packageName);
    if (!found) return err(new Error(`Package "${packageName}" not found`));
    return ok(found);
  }

  /** Get featured packages */
  async getFeatured(): Promise<Result<MarketplaceListing[]>> {
    await this.loadIndex();
    return ok(this.index.filter(l => l.featured));
  }

  /** Get categories */
  async getCategories(): Promise<string[]> {
    return CATEGORIES;
  }

  /** Sync registry index from GitHub to local cache */
  async syncIndex(): Promise<Result<{ totalPackages: number }>> {
    try {
      const url = `https://raw.githubusercontent.com/${this.registryRepo}/main/registry/index.json`;
      const response = await fetch(url);
      if (!response.ok) {
        return err(new Error(`Failed to fetch index: HTTP ${response.status}`));
      }

      const data = await response.json() as MarketplaceListing[];
      this.index = data;

      // Cache locally
      await fs.mkdir(this.cacheDir, { recursive: true });
      await fs.writeFile(
        join(this.cacheDir, 'index.json'),
        JSON.stringify(data, null, 2),
        'utf-8',
      );

      return ok({ totalPackages: data.length });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Load index from local cache */
  private async loadIndex(): Promise<void> {
    if (this.index.length > 0) return;
    try {
      const content = await fs.readFile(join(this.cacheDir, 'index.json'), 'utf-8');
      this.index = JSON.parse(content) as MarketplaceListing[];
    } catch {
      this.index = [];
    }
  }
}
