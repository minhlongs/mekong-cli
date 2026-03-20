/**
 * Redis Client & Connection Pool
 * Centralized Redis client configuration for algo-trader
 */

import Redis from 'ioredis';

export interface RedisConfig {
  host: string;
  port: number;
  password?: string;
  db?: number;
  maxRetriesPerRequest: number;
  retryDelayOnFailover: number;
}

const DEFAULT_CONFIG: RedisConfig = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  db: parseInt(process.env.REDIS_DB || '0'),
  maxRetriesPerRequest: 3,
  retryDelayOnFailover: 100,
};

// Main connection for general operations
let mainClient: Redis | null = null;

// Pub/Sub separate connections (required by Redis)
let pubClient: Redis | null = null;
let subClient: Redis | null = null;

export function getRedisClient(): Redis {
  if (!mainClient) {
    mainClient = new Redis(DEFAULT_CONFIG);
    mainClient.on('error', (err) => console.error('[Redis] Error:', err));
    mainClient.on('connect', () => console.log('[Redis] Connected'));
  }
  return mainClient;
}

export function getPubClient(): Redis {
  if (!pubClient) {
    pubClient = new Redis({ ...DEFAULT_CONFIG, db: DEFAULT_CONFIG.db });
  }
  return pubClient;
}

export function getSubClient(): Redis {
  if (!subClient) {
    subClient = new Redis({ ...DEFAULT_CONFIG, db: DEFAULT_CONFIG.db });
  }
  return subClient;
}

export async function closeRedisConnections(): Promise<void> {
  await Promise.all([
    mainClient?.quit(),
    pubClient?.quit(),
    subClient?.quit(),
  ]);
  mainClient = null;
  pubClient = null;
  subClient = null;
}

export { Redis };
