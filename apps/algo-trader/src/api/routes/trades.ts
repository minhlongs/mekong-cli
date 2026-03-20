/**
 * Trades Routes
 * GET /trades - List all trades
 * GET /trades/:id - Get trade by ID
 */

import { Router, Request, Response } from 'express';
import { TradeRepository } from '../../db/trade-repository';

export const tradesRouter: Router = Router();
const tradeRepo = new TradeRepository();

/**
 * GET /trades
 * Query params: limit (default 100), offset (default 0)
 */
tradesRouter.get('/', async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 100;
    const offset = parseInt(req.query.offset as string) || 0;

    const trades = await tradeRepo.getRecent(limit);
    res.json({
      data: trades.slice(offset, offset + limit),
      total: trades.length,
      limit,
      offset,
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to fetch trades',
    });
  }
});

/**
 * GET /trades/:id
 */
tradesRouter.get('/:id', async (req: Request, res: Response) => {
  try {
    const tradeId = Array.isArray(req.params.id) ? req.params.id[0] : req.params.id;
    const trade = await tradeRepo.getById(tradeId);

    if (!trade) {
      return res.status(404).json({ error: 'Trade not found' });
    }

    res.json(trade);
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to fetch trade',
    });
  }
});
