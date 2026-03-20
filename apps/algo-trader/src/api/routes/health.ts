/**
 * Health Routes
 * GET /health - Health check
 * GET /metrics - System metrics
 */

import { Router, Request, Response } from 'express';
import { getRedisClient } from '../../redis';
import { getDbClient } from '../../db/postgres-client';

export const healthRouter: Router = Router();

/**
 * GET /health
 */
healthRouter.get('/', async (req: Request, res: Response) => {
  try {
    // Check Redis
    const redis = getRedisClient();
    await redis.ping();
    const redisOk = true;
  } catch (error) {
    return res.status(503).json({
      status: 'unhealthy',
      redis: 'error',
      error: error instanceof Error ? error.message : 'Redis ping failed',
    });
  }

  // Check PostgreSQL (optional - may not be connected)
  let postgresOk = 'disconnected';
  try {
    const db = getDbClient();
    await db.query('SELECT 1');
    postgresOk = 'ok';
  } catch (error) {
    postgresOk = 'error';
  }

  res.json({
    status: 'healthy',
    redis: 'ok',
    postgres: postgresOk,
    timestamp: Date.now(),
    uptime: process.uptime(),
  });
});

/**
 * GET /metrics
 */
healthRouter.get('/metrics', async (req: Request, res: Response) => {
  try {
    const redis = getRedisClient();

    // Get Redis info
    const redisInfo = await redis.info('memory');
    const memoryMatch = redisInfo.match(/used_memory:(\d+)/);
    const redisMemory = memoryMatch ? parseInt(memoryMatch[1]) : 0;

    // Get key counts
    const arbitrageKeys = (await redis.keys('arbitrage:*')).length;
    const positionKeys = (await redis.keys('position:*')).length;
    const signalKeys = (await redis.keys('signal:*')).length;

    res.json({
      redis: {
        memoryBytes: redisMemory,
        memoryMB: (redisMemory / 1024 / 1024).toFixed(2),
      },
      keys: {
        arbitrage: arbitrageKeys,
        positions: positionKeys,
        signals: signalKeys,
      },
      process: {
        memoryMB: (process.memoryUsage().heapUsed / 1024 / 1024).toFixed(2),
        uptime: process.uptime(),
      },
      timestamp: Date.now(),
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to fetch metrics',
    });
  }
});
