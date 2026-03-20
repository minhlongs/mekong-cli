/**
 * Signals Routes
 * GET /signals - Get current arbitrage signals
 */

import { Router, Request, Response } from 'express';
import { getRedisClient } from '../../redis';

export const signalsRouter: Router = Router();
const redis = getRedisClient();

/**
 * GET /signals
 * Query params: minSpread (default 0), limit (default 50)
 */
signalsRouter.get('/', async (req: Request, res: Response) => {
  try {
    const minSpread = parseFloat(req.query.minSpread as string) || 0;
    const limit = parseInt(req.query.limit as string) || 50;

    // Get all arbitrage opportunities from Redis
    const keys = await redis.keys('arbitrage:*');
    const signals: any[] = [];

    for (const key of keys) {
      const data = await redis.hgetall(key);
      if (data && data.spreadPercent) {
        const spread = parseFloat(data.spreadPercent);
        if (spread >= minSpread) {
          signals.push({
            id: data.id,
            symbol: data.symbol,
            buyExchange: data.buyExchange,
            sellExchange: data.sellExchange,
            buyPrice: parseFloat(data.buyPrice),
            sellPrice: parseFloat(data.sellPrice),
            spread,
            latency: parseInt(data.latency),
            timestamp: parseInt(data.timestamp),
          });
        }
      }
    }

    // Sort by spread descending and limit
    signals.sort((a, b) => b.spread - a.spread);
    res.json({
      data: signals.slice(0, limit),
      count: signals.length,
      limit,
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to fetch signals',
    });
  }
});
