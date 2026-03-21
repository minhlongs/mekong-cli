/**
 * Core HTTP layer — fetch wrapper with retry + auth for MekongClient
 */

import { createApiError, MekongNetworkError } from './errors.js';

export interface RequesterConfig {
  baseUrl: string;
  getApiKey: () => string | undefined;
  getJwt: () => string | undefined;
  maxRetries: number;
  timeoutMs: number;
}

export class HttpRequester {
  constructor(private readonly config: RequesterConfig) {}

  private buildHeaders(): Record<string, string> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    const jwt = this.config.getJwt();
    const apiKey = this.config.getApiKey();
    if (jwt) {
      headers['Authorization'] = `Bearer ${jwt}`;
    } else if (apiKey) {
      headers['X-API-Key'] = apiKey;
    }
    return headers;
  }

  async request<T>(
    method: string,
    path: string,
    body?: unknown,
    query?: Record<string, string | number | undefined>,
  ): Promise<T> {
    let url = `${this.config.baseUrl}${path}`;

    if (query) {
      const params = new URLSearchParams();
      for (const [k, v] of Object.entries(query)) {
        if (v !== undefined) params.set(k, String(v));
      }
      const qs = params.toString();
      if (qs) url += `?${qs}`;
    }

    let attempt = 0;
    while (true) {
      attempt++;
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this.config.timeoutMs);

        let res: Response;
        try {
          const init: RequestInit = {
            method,
            headers: this.buildHeaders(),
            signal: controller.signal,
          };
          if (body !== undefined) init.body = JSON.stringify(body);
          res = await fetch(url, init);
        } finally {
          clearTimeout(timer);
        }

        if (res.ok) return res.json() as Promise<T>;

        let errBody: { error?: string; code?: string } = {};
        try { errBody = await res.json() as typeof errBody; } catch { /* ignore */ }

        const apiErr = createApiError(res.status, errBody);
        if (res.status >= 500 && attempt < this.config.maxRetries) {
          await sleep(exponentialDelay(attempt));
          continue;
        }
        throw apiErr;
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          throw new MekongNetworkError(`Request timed out after ${this.config.timeoutMs}ms`, err);
        }
        if (err instanceof Error && err.name.startsWith('Mekong')) throw err;
        if (attempt < this.config.maxRetries) {
          await sleep(exponentialDelay(attempt));
          continue;
        }
        throw new MekongNetworkError('Network request failed', err);
      }
    }
  }

  get<T>(path: string, query?: Record<string, string | number | undefined>): Promise<T> {
    return this.request<T>('GET', path, undefined, query);
  }

  post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>('POST', path, body);
  }

  put<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>('PUT', path, body);
  }

  del<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path);
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function exponentialDelay(attempt: number): number {
  return Math.min(500 * Math.pow(2, attempt - 1), 8_000);
}
