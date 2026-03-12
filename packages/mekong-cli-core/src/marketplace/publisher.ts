/**
 * Marketplace Publisher — publish SOP packages to GitHub-based registry.
 * Uses GitHub Releases API as storage (free, no server needed).
 * ROI: Operational ROI — enables paid SOP distribution via marketplace.
 */
import { promises as fs } from 'fs';
import type { SopPackage } from './types.js';
import { ok, err } from '../types/common.js';
import type { Result } from '../types/common.js';


export class MarketplacePublisher {
  private readonly registryRepo: string;
  private readonly githubToken?: string;

  constructor(config: { registryRepo: string; githubTokenEnv?: string }) {
    this.registryRepo = config.registryRepo;
    this.githubToken = config.githubTokenEnv ? process.env[config.githubTokenEnv] : undefined;
  }

  /** Publish package to marketplace */
  async publish(mkgPath: string): Promise<Result<{ url: string }>> {
    if (!this.githubToken) {
      return err(new Error('GitHub token required for publishing. Set GITHUB_TOKEN env var.'));
    }

    try {
      // Read and validate the .mkg file
      const content = await fs.readFile(mkgPath, 'utf-8');
      const data = JSON.parse(content) as { package: SopPackage; files: Record<string, string> };
      const pkg = data.package;

      if (!pkg.name || !pkg.version) {
        return err(new Error('Invalid package: missing name or version'));
      }

      // Create GitHub release tag
      const tag = `${pkg.name.replace('/', '-')}-v${pkg.version}`;
      const releaseUrl = `https://api.github.com/repos/${this.registryRepo}/releases`;

      const response = await fetch(releaseUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.githubToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/vnd.github.v3+json',
        },
        body: JSON.stringify({
          tag_name: tag,
          name: `${pkg.name}@${pkg.version}`,
          body: `${pkg.description}\n\nCategory: ${pkg.category}\nAuthor: ${pkg.author.name}`,
          draft: false,
          prerelease: false,
        }),
      });

      if (!response.ok) {
        const body = await response.text();
        return err(new Error(`GitHub API error ${response.status}: ${body}`));
      }

      const release = await response.json() as { html_url: string };
      return ok({ url: release.html_url });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Unpublish a version */
  async unpublish(packageName: string, version: string): Promise<Result<void>> {
    if (!this.githubToken) {
      return err(new Error('GitHub token required for unpublishing'));
    }

    try {
      const tag = `${packageName.replace('/', '-')}-v${version}`;
      const url = `https://api.github.com/repos/${this.registryRepo}/releases/tags/${tag}`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${this.githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
        },
      });

      if (!response.ok) {
        return err(new Error(`Release not found: ${tag}`));
      }

      const release = await response.json() as { id: number };
      const deleteUrl = `https://api.github.com/repos/${this.registryRepo}/releases/${release.id}`;

      await fetch(deleteUrl, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
        },
      });

      return ok(undefined);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
