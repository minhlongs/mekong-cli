import { execSync } from 'child_process';
import { GitHubViewerResponse } from '../types/github.types';
import { GitHubAPIError, NetworkError, AuthenticationError } from './errors';
import { withRetry } from './retry-with-exponential-backoff';
import { validateGitHubToken } from './input-validation';

export class GitHubClient {
  private token: string | null = null;
  private readonly apiUrl = 'https://api.github.com/graphql';

  constructor(token?: string) {
    if (token) {
      // Validate token format
      validateGitHubToken(token);
      this.token = token;
    }
  }

  /**
   * authenticates the client using environment variable or gh CLI
   */
  public async authenticate(): Promise<void> {
    if (this.token) return;

    // 1. Try environment variable
    if (process.env.GITHUB_TOKEN) {
      validateGitHubToken(process.env.GITHUB_TOKEN);
      this.token = process.env.GITHUB_TOKEN;
      return;
    }

    // 2. Try gh CLI
    try {
      const output = execSync('gh auth token', { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] });
      const token = output.trim();
      validateGitHubToken(token);
      this.token = token;
    } catch (error) {
      throw new AuthenticationError(
        'Authentication failed: No GITHUB_TOKEN provided and gh CLI lookup failed. ' +
        'Please set GITHUB_TOKEN environment variable or run "gh auth login".'
      );
    }
  }

  /**
   * Executes a GraphQL query against the GitHub API with retry logic
   */
  public async graphql<T>(query: string, variables: Record<string, any> = {}): Promise<T> {
    if (!this.token) {
      await this.authenticate();
    }

    if (!this.token) {
       throw new AuthenticationError('Client is not authenticated.');
    }

    return withRetry(async () => {
      try {
        const response = await fetch(this.apiUrl, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json',
            'User-Agent': 'mekong-cli-vibe-dev'
          },
          body: JSON.stringify({ query, variables })
        });

        // Extract rate limit headers
        const rateLimitRemaining = parseInt(response.headers.get('x-ratelimit-remaining') || '0');
        const rateLimitReset = parseInt(response.headers.get('x-ratelimit-reset') || '0');

        if (!response.ok) {
          // Handle specific HTTP errors
          if (response.status === 401) {
            throw new AuthenticationError('Invalid GitHub token. Please check your credentials.');
          }

          if (response.status === 403 || response.status === 429) {
            throw new GitHubAPIError(
              `Rate limit exceeded. Reset at ${new Date(rateLimitReset * 1000).toISOString()}`,
              response.status,
              rateLimitRemaining
            );
          }

          throw new NetworkError(`HTTP ${response.status}: ${response.statusText}`);
        }

        const body = await response.json() as { data: T; errors?: any[] };

        if (body.errors && body.errors.length > 0) {
          const errorMessages = body.errors.map((e: any) => e.message).join(', ');
          throw new GitHubAPIError(`GraphQL Error: ${errorMessages}`, response.status);
        }

        return body.data;

      } catch (error) {
         if (error instanceof GitHubAPIError || error instanceof AuthenticationError || error instanceof NetworkError) {
           throw error;
         }
         if (error instanceof Error) {
           throw new NetworkError(error.message);
         }
         throw new NetworkError('Unknown error occurred during GraphQL request');
      }
    }, {
      maxAttempts: 3,
      initialDelay: 1000,
      maxDelay: 5000
    });
  }

  /**
   * Verifies connection by fetching the authenticated viewer
   */
  public async getViewer(): Promise<GitHubViewerResponse['data']['viewer']> {
    const query = `
      query {
        viewer {
          login
          name
          id
        }
      }
    `;

    const data = await this.graphql<{ viewer: GitHubViewerResponse['data']['viewer'] }>(query);
    return data.viewer;
  }
}
