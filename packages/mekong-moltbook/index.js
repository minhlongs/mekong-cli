'use strict';

const MOLTBOOK_HOST = 'www.moltbook.com';
const DEFAULT_BASE_URL = `https://${MOLTBOOK_HOST}/api/v1`;
const RETRY_LIMIT = 3;

/**
 * MoltbookClient — thin client for Moltbook AI agent social network.
 * Reference: moltbook.com
 * Requires Node 18+ (native fetch).
 */
class MoltbookClient {
  /**
   * @param {Object} config
   * @param {string} config.apiKey   - Moltbook API key
   * @param {string} [config.baseUrl] - Defaults to https://www.moltbook.com/api/v1
   */
  constructor({ apiKey, baseUrl = DEFAULT_BASE_URL } = {}) {
    if (!apiKey) throw new Error('MoltbookClient: apiKey is required');
    const url = new URL(baseUrl);
    if (url.hostname !== MOLTBOOK_HOST) {
      throw new Error(`MoltbookClient: baseUrl must point to ${MOLTBOOK_HOST}`);
    }
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  /** @private */
  _headers() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.apiKey}`,
    };
  }

  /** @private */
  async _request(method, endpoint, body, attempt = 1) {
    const url = `${this.baseUrl}${endpoint}`;
    const opts = { method, headers: this._headers() };
    if (body !== undefined) opts.body = JSON.stringify(body);

    const res = await fetch(url, opts);

    if (res.status === 429 && attempt <= RETRY_LIMIT) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '5', 10);
      await new Promise(r => setTimeout(r, retryAfter * 1000));
      return this._request(method, endpoint, body, attempt + 1);
    }

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Moltbook ${method} ${endpoint} → ${res.status}: ${text}`);
    }

    const ct = res.headers.get('content-type') || '';
    return ct.includes('application/json') ? res.json() : res.text();
  }

  /** Register this agent on Moltbook. */
  register(name, description) {
    return this._request('POST', '/agents/register', { name, description });
  }

  /** Get the authenticated agent's profile. */
  getProfile() {
    return this._request('GET', '/agents/me');
  }

  /** Update the authenticated agent's profile. */
  updateProfile(data) {
    return this._request('PATCH', '/agents/me', data);
  }

  /**
   * Create a new post.
   * @param {string} title
   * @param {string} body
   * @param {string} submolt - Submolt/community name
   */
  createPost(title, body, submolt) {
    return this._request('POST', '/posts', { title, body, submolt });
  }

  /** Get the agent's feed. */
  getFeed() {
    return this._request('GET', '/feed');
  }

  /** Upvote a post by ID. */
  upvote(postId) {
    if (!postId) throw new Error('upvote: postId is required');
    return this._request('POST', `/posts/${postId}/upvote`);
  }

  /**
   * Fetch HEARTBEAT.md and return its content with a timestamp update.
   * @returns {{ content: string, fetchedAt: string }}
   */
  async heartbeat() {
    const res = await fetch(`https://${MOLTBOOK_HOST}/HEARTBEAT.md`);
    const content = await res.text();
    return { content, fetchedAt: new Date().toISOString() };
  }
}

module.exports = { MoltbookClient };
