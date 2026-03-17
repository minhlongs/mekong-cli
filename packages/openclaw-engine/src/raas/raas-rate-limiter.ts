/**
 * raas-rate-limiter.ts — Token bucket rate limiter per tenant/tier
 * Returns X-RateLimit-* compatible headers.
 */
import type { RaasTier } from './raas-pricing.js';
import type { ApiResponse } from './raas-api.js';

// --- Types ---

export interface RateLimitConfig {
  maxTokens: number;     // bucket capacity
  refillRate: number;    // tokens per second
  windowMs: number;      // window for header display
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  limit: number;
  resetAt: number;       // epoch ms when bucket refills
  retryAfterMs: number;  // 0 if allowed
}

export interface RateLimitHeaders {
  'X-RateLimit-Limit': string;
  'X-RateLimit-Remaining': string;
  'X-RateLimit-Reset': string;
  'Retry-After'?: string;
}

// --- Tier Rate Limits ---

const TIER_RATE_LIMITS: Record<RaasTier, RateLimitConfig> = {
  starter: { maxTokens: 100, refillRate: 100 / 60, windowMs: 60_000 },
  pro: { maxTokens: 1000, refillRate: 1000 / 60, windowMs: 60_000 },
  enterprise: { maxTokens: 100_000, refillRate: 100_000 / 60, windowMs: 60_000 },
};

// --- Token Bucket State ---

interface BucketState {
  tokens: number;
  lastRefill: number;
  tier: RaasTier;
}

const buckets = new Map<string, BucketState>();

/** Get or create a token bucket for a tenant */
function getBucket(tenantId: string, tier: RaasTier): BucketState {
  let bucket = buckets.get(tenantId);
  if (!bucket) {
    const config = TIER_RATE_LIMITS[tier];
    bucket = { tokens: config.maxTokens, lastRefill: Date.now(), tier };
    buckets.set(tenantId, bucket);
  }
  return bucket;
}

/** Refill tokens based on elapsed time */
function refillBucket(bucket: BucketState): void {
  const config = TIER_RATE_LIMITS[bucket.tier];
  const now = Date.now();
  const elapsed = (now - bucket.lastRefill) / 1000; // seconds
  const refill = elapsed * config.refillRate;
  bucket.tokens = Math.min(config.maxTokens, bucket.tokens + refill);
  bucket.lastRefill = now;
}

// --- Core Functions ---

/** Check rate limit for a tenant. Consumes 1 token if allowed. */
export function checkRateLimit(tenantId: string, tier: RaasTier): RateLimitResult {
  const config = TIER_RATE_LIMITS[tier];
  const bucket = getBucket(tenantId, tier);

  refillBucket(bucket);

  if (bucket.tokens >= 1) {
    bucket.tokens -= 1;
    return {
      allowed: true,
      remaining: Math.floor(bucket.tokens),
      limit: config.maxTokens,
      resetAt: bucket.lastRefill + config.windowMs,
      retryAfterMs: 0,
    };
  }

  // Denied — calculate retry time
  const timeToRefill = Math.ceil(1 / config.refillRate * 1000);
  return {
    allowed: false,
    remaining: 0,
    limit: config.maxTokens,
    resetAt: bucket.lastRefill + config.windowMs,
    retryAfterMs: timeToRefill,
  };
}

/** Build HTTP-compatible rate limit headers */
export function buildRateLimitHeaders(result: RateLimitResult): RateLimitHeaders {
  const headers: RateLimitHeaders = {
    'X-RateLimit-Limit': String(result.limit),
    'X-RateLimit-Remaining': String(result.remaining),
    'X-RateLimit-Reset': String(Math.ceil(result.resetAt / 1000)),
  };
  if (!result.allowed) {
    headers['Retry-After'] = String(Math.ceil(result.retryAfterMs / 1000));
  }
  return headers;
}

/** Get tier rate limit config (for display) */
export function getTierRateLimit(tier: RaasTier): RateLimitConfig {
  return TIER_RATE_LIMITS[tier];
}

/** Reset a tenant's rate limit bucket */
export function resetRateLimit(tenantId: string): boolean {
  return buckets.delete(tenantId);
}

/** Get current bucket state (for monitoring) */
export function getRateLimitStatus(tenantId: string, tier: RaasTier): { tokens: number; maxTokens: number } {
  const bucket = getBucket(tenantId, tier);
  refillBucket(bucket);
  const config = TIER_RATE_LIMITS[tier];
  return { tokens: Math.floor(bucket.tokens), maxTokens: config.maxTokens };
}
