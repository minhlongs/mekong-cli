/**
 * Redis-backed Rate Limiting Store & Configuration
 */

import Redis from 'ioredis'
import { securityLogger } from './logger'

export interface RateLimitConfig {
  interval: number // Time window in milliseconds
  maxRequests: number // Max requests per interval
  blockDuration?: number // How long to block after limit exceeded (ms)
}

export interface RateLimitResult {
  allowed: boolean
  remaining: number
  resetAt: Date
  blockedUntil?: Date
}

export const RATE_LIMITS: Record<string, RateLimitConfig> = {
  'api:default': { interval: 60_000, maxRequests: 100 },
  'api:auth': { interval: 60_000, maxRequests: 10, blockDuration: 300_000 },
  'api:billing': { interval: 60_000, maxRequests: 20 },
  'api:analytics': { interval: 60_000, maxRequests: 50 },
  'action:login': { interval: 300_000, maxRequests: 5, blockDuration: 900_000 },
  'action:signup': { interval: 3600_000, maxRequests: 3, blockDuration: 3600_000 },
  'action:password-reset': { interval: 3600_000, maxRequests: 3 },
  'action:invite': { interval: 3600_000, maxRequests: 10 },
  'webhook:stripe': { interval: 60_000, maxRequests: 100 },
  'webhook:payos': { interval: 60_000, maxRequests: 100 },
}

let redisClient: Redis | null = null

export function getRedisClient(): Redis {
  if (!redisClient) {
    redisClient = new Redis({
      host: process.env.REDIS_HOST || 'redis.internal',
      port: parseInt(process.env.REDIS_PORT || '6379'),
      password: process.env.REDIS_PASSWORD,
      maxRetriesPerRequest: 3,
      lazyConnect: true,
      tls: process.env.NODE_ENV === 'production' ? {} : undefined,
    })
    redisClient.on('error', () => {})
    redisClient.on('connect', () => {})
  }
  return redisClient
}

export class RedisRateLimiter {
  private redis: Redis

  constructor() {
    this.redis = getRedisClient()
  }

  private getKey(identifier: string, limitType: string): string {
    return `ratelimit:${limitType}:${identifier}`
  }

  private getBlockKey(identifier: string, limitType: string): string {
    return `ratelimit:block:${limitType}:${identifier}`
  }

  async check(identifier: string, limitType: string): Promise<RateLimitResult> {
    const config = RATE_LIMITS[limitType] || RATE_LIMITS['api:default']
    const key = this.getKey(identifier, limitType)
    const blockKey = this.getBlockKey(identifier, limitType)
    const now = Date.now()

    try {
      const blockedUntil = await this.redis.get(blockKey)
      if (blockedUntil) {
        const blockedTime = parseInt(blockedUntil)
        if (blockedTime > now) {
          return {
            allowed: false,
            remaining: 0,
            resetAt: new Date(blockedTime),
            blockedUntil: new Date(blockedTime),
          }
        }
        await this.redis.del(blockKey)
      }

      const pipeline = this.redis.pipeline()
      pipeline.incr(key)
      pipeline.expire(key, Math.ceil(config.interval / 1000))
      const results = await pipeline.exec()
      const count = (results?.[0]?.[1] as number) || 1

      if (count > config.maxRequests) {
        if (config.blockDuration) {
          const blockUntil = now + config.blockDuration
          await this.redis.setex(blockKey, Math.ceil(config.blockDuration / 1000), String(blockUntil))
          return {
            allowed: false,
            remaining: 0,
            resetAt: new Date(blockUntil),
            blockedUntil: new Date(blockUntil),
          }
        }
        return { allowed: false, remaining: 0, resetAt: new Date(now + config.interval) }
      }

      return {
        allowed: true,
        remaining: Math.max(0, config.maxRequests - count),
        resetAt: new Date(now + config.interval),
      }
    } catch (error) {
      await securityLogger.error(
        'Rate limiting error, allowing request',
        error instanceof Error ? error : new Error(String(error))
      )
      return {
        allowed: true,
        remaining: config.maxRequests - 1,
        resetAt: new Date(now + config.interval),
      }
    }
  }

  async reset(identifier: string, limitType: string): Promise<void> {
    const key = this.getKey(identifier, limitType)
    const blockKey = this.getBlockKey(identifier, limitType)
    try {
      await this.redis.del(key, blockKey)
    } catch (error) {
      await securityLogger.error(
        'Error resetting rate limit',
        error instanceof Error ? error : new Error(String(error))
      )
    }
  }

  async getStats(
    identifier: string,
    limitType: string
  ): Promise<{
    current: number
    remaining: number
    resetAt: Date
    isBlocked: boolean
    blockedUntil?: Date
  }> {
    const key = this.getKey(identifier, limitType)
    const blockKey = this.getBlockKey(identifier, limitType)
    const config = RATE_LIMITS[limitType] || RATE_LIMITS['api:default']
    const now = Date.now()

    try {
      const [count, blockedUntil] = await this.redis.mget(key, blockKey)
      const current = parseInt(count || '0')
      const blockedTime = blockedUntil ? parseInt(blockedUntil) : 0
      const isBlocked = blockedTime > now

      return {
        current,
        remaining: Math.max(0, config.maxRequests - current),
        resetAt: new Date(now + config.interval),
        isBlocked,
        blockedUntil: isBlocked ? new Date(blockedTime) : undefined,
      }
    } catch (error) {
      await securityLogger.error(
        'Error getting rate limit stats',
        error instanceof Error ? error : new Error(String(error))
      )
      return { current: 0, remaining: config.maxRequests, resetAt: new Date(now + config.interval), isBlocked: false }
    }
  }
}
