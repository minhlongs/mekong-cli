import { PaperTradingPolymarketAdapter } from '../../src/execution/paper-trading-polymarket-adapter';
import * as fs from 'fs';
import * as path from 'path';

const PAPER_TRADES_PATH = path.resolve(process.cwd(), 'data', 'paper-trades.json');

describe('PaperTradingPolymarketAdapter', () => {
  let adapter: PaperTradingPolymarketAdapter;

  beforeEach(() => {
    // Clean paper trades file before each test to avoid cross-test contamination
    try { if (fs.existsSync(PAPER_TRADES_PATH)) fs.unlinkSync(PAPER_TRADES_PATH); } catch {}
    adapter = new PaperTradingPolymarketAdapter();
  });

  it('should connect without error', async () => {
    await expect(adapter.connect()).resolves.toBeUndefined();
    expect(adapter.isConnected()).toBe(true);
  });

  it('should place paper limit order and return matched status', async () => {
    const order = await adapter.placeLimitOrder('token-1', 0.55, 100, 'BUY');
    expect(order.orderId).toContain('paper_');
    expect(order.status).toBe('matched');
    expect(order.price).toBe(0.55);
    expect(order.size).toBe(100);
  });

  it('should reject invalid price', async () => {
    await expect(adapter.placeLimitOrder('t', 0, 10, 'BUY')).rejects.toThrow('Invalid price');
    await expect(adapter.placeLimitOrder('t', 1, 10, 'BUY')).rejects.toThrow('Invalid price');
    await expect(adapter.placeLimitOrder('t', 1.5, 10, 'BUY')).rejects.toThrow('Invalid price');
  });

  it('should track position after BUY', async () => {
    await adapter.placeLimitOrder('token-1', 0.50, 100, 'BUY');
    const positions = adapter.getPositions();
    expect(positions.get('token-1')).toEqual({ size: 100, avgPrice: 0.50, side: 'BUY' });
  });

  it('should realize PnL on closing trade', async () => {
    await adapter.placeLimitOrder('token-1', 0.50, 100, 'BUY');
    await adapter.placeLimitOrder('token-1', 0.60, 100, 'SELL');

    const pnl = adapter.getPnL();
    // Profit: (0.60 - 0.50) * 100 = $10
    expect(pnl.realizedPnl).toBeCloseTo(10, 2);
    expect(pnl.tradeCount).toBe(2);
  });

  it('should calculate unrealized PnL from ticks', async () => {
    await adapter.placeLimitOrder('token-1', 0.50, 100, 'BUY');

    adapter.updateTick({
      exchange: 'polymarket', symbol: 'market-1', tokenId: 'token-1',
      bid: 0.55, ask: 0.57, spread: 0.02, timestamp: Date.now(),
    });

    const pnl = adapter.getPnL();
    // Unrealized: (bid 0.55 - entry 0.50) * 100 = $5
    expect(pnl.unrealizedPnl).toBeCloseTo(5, 2);
    expect(pnl.totalPnl).toBeCloseTo(5, 2);
  });

  it('should average price on adding to position', async () => {
    await adapter.placeLimitOrder('token-1', 0.40, 50, 'BUY');
    await adapter.placeLimitOrder('token-1', 0.60, 50, 'BUY');

    const pos = adapter.getPositions().get('token-1');
    expect(pos?.avgPrice).toBeCloseTo(0.50, 4);
    expect(pos?.size).toBe(100);
  });

  it('should record trades in getTrades()', async () => {
    await adapter.placeLimitOrder('t1', 0.50, 10, 'BUY');
    await adapter.placeLimitOrder('t2', 0.30, 20, 'SELL');

    const trades = adapter.getTrades();
    expect(trades).toHaveLength(2);
    expect(trades[0].tokenId).toBe('t1');
    expect(trades[1].side).toBe('SELL');
  });

  it('cancelOrder should be no-op', async () => {
    await expect(adapter.cancelOrder('any')).resolves.toBeUndefined();
    await expect(adapter.cancelAllOrders()).resolves.toBeUndefined();
  });

  it('should use market tick price for market orders', async () => {
    adapter.updateTick({
      exchange: 'polymarket', symbol: 'm', tokenId: 'token-1',
      bid: 0.48, ask: 0.52, spread: 0.04, timestamp: Date.now(),
    });

    const order = await adapter.placeMarketOrder('token-1', 50, 'BUY');
    expect(order.price).toBe(0.52); // Ask price for BUY
  });
});
