/**
 * Polymarket Exchange Adapter
 *
 * Adapts Polymarket CLOB client to work with LiveExchangeManager architecture.
 * Provides unified interface for order placement, cancellation, and market data.
 */

import { EventEmitter } from 'events';
import {
  PolymarketClobClient,
  PolymarketWebSocket,
  PolymarketGammaClient,
  OrderType,
  Side,
  type PolymarketClientConfig,
  type TradeEvent,
  type BestBidAskEvent,
} from '../polymarket';
import { logger } from '../utils/logger';

/** Wrap a promise with a timeout to prevent indefinite hangs on API calls */
function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`[Timeout] ${label} exceeded ${ms}ms`)), ms),
    ),
  ]);
}

/** Default API call timeout (10 seconds) */
const API_TIMEOUT_MS = 10_000;
/** Max slippage allowed (0.5% = 50 BPS) — reject if mid-price deviates more */
const MAX_SLIPPAGE_BPS = 50;

export interface PolymarketOrder {
  orderId: string;
  tokenId: string;
  side: 'BUY' | 'SELL';
  price: number;
  size: number;
  status: 'live' | 'matched' | 'cancelled' | 'expired';
  createdAt: number;
}

export interface PolymarketTick {
  exchange: string;
  symbol: string; // conditionId or market slug
  tokenId: string;
  bid: number;
  ask: number;
  spread: number;
  timestamp: number;
}

export interface PolymarketAdapterConfig extends PolymarketClientConfig {
  markets?: string[]; // Market IDs to subscribe to
  autoHeartbeat?: boolean; // Default true
}

export class PolymarketAdapter extends EventEmitter {
  private clobClient: PolymarketClobClient;
  private wsClient: PolymarketWebSocket | null = null;
  private gammaClient: PolymarketGammaClient;
  private config: Required<PolymarketAdapterConfig>;
  private running = false;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private activeOrders = new Map<string, PolymarketOrder>();
  private latestTicks = new Map<string, PolymarketTick>(); // key: tokenId

  constructor(config: PolymarketAdapterConfig = {}) {
    super();
    this.config = {
      privateKey: config.privateKey || '',
      apiKey: config.apiKey || '',
      apiSecret: config.apiSecret || '',
      apiPassphrase: config.apiPassphrase || '',
      signatureType: config.signatureType || 0,
      useServerTime: config.useServerTime || false,
      throwOnError: config.throwOnError !== false,
      autoHeartbeat: config.autoHeartbeat !== false,
      markets: config.markets || [],
      funderAddress: config.funderAddress || '',
    };

    this.clobClient = new PolymarketClobClient(config);
    this.gammaClient = new PolymarketGammaClient();
  }

  /**
   * Initialize connection (no auth required for market data)
   */
  async connect(): Promise<void> {
    if (this.running) return;

    logger.info('[Polymarket] Connecting...');

    // Initialize WebSocket for real-time data
    this.wsClient = new PolymarketWebSocket('market');

    // Wire up WebSocket events
    this.wsClient.onBestBidAsk = (event: BestBidAskEvent) => {
      this.handleBestBidAsk(event);
    };

    this.wsClient.onTrade = (event: TradeEvent) => {
      this.emit('trade', event);
    };

    this.wsClient.onError = (err: Error) => {
      logger.error('[Polymarket] WS Error:', err.message);
      this.emit('error', err);
    };

    this.wsClient.onDisconnect = () => {
      logger.warn('[Polymarket] WebSocket disconnected');
      this.emit('disconnect', { exchange: 'polymarket' });
    };

    // Connect WebSocket
    this.wsClient.connect(undefined, this.config.markets);

    // Start heartbeat if enabled and we have credentials
    if (this.config.autoHeartbeat && this.clobClient.isReady()) {
      this.startHeartbeat();
    }

    this.running = true;
    logger.info('[Polymarket] Connected');
    this.emit('connect', { exchange: 'polymarket' });
  }

  /**
   * Disconnect and cleanup
   */
  async disconnect(): Promise<void> {
    if (!this.running) return;
    this.running = false;

    this.stopHeartbeat();
    this.wsClient?.disconnect();
    this.wsClient = null;
    this.activeOrders.clear();

    logger.info('[Polymarket] Disconnected');
    this.emit('disconnect', { exchange: 'polymarket' });
  }

  /**
   * Place a limit order
   */
  async placeLimitOrder(
    tokenId: string,
    price: number,
    size: number,
    side: 'BUY' | 'SELL',
    orderType: OrderType.GTC | OrderType.GTD = OrderType.GTC,
    expiration?: number,
  ): Promise<PolymarketOrder> {
    if (!this.clobClient.isReady()) {
      throw new Error('Polymarket client not authenticated - provide API credentials');
    }

    // Slippage protection: verify price is within MAX_SLIPPAGE_BPS of current market
    const tick = this.latestTicks.get(tokenId);
    if (tick) {
      const midPrice = (tick.bid + tick.ask) / 2;
      if (midPrice > 0) {
        const slippageBps = Math.abs(price - midPrice) / midPrice * 10000;
        if (slippageBps > MAX_SLIPPAGE_BPS) {
          throw new Error(
            `Slippage ${slippageBps.toFixed(0)} BPS exceeds max ${MAX_SLIPPAGE_BPS} BPS ` +
            `(price=${price}, mid=${midPrice.toFixed(4)}, token=${tokenId})`
          );
        }
      }
    }

    // Validate order parameters
    if (price <= 0 || price >= 1) throw new Error(`Invalid price ${price}: must be (0, 1)`);
    if (size <= 0) throw new Error(`Invalid size ${size}: must be > 0`);
    if (isNaN(price) || isNaN(size)) throw new Error('Price or size is NaN');

    const response = await withTimeout(
      this.clobClient.createAndPostLimitOrder(tokenId, price, size, side, orderType, expiration),
      API_TIMEOUT_MS,
      'placeLimitOrder',
    );

    const order: PolymarketOrder = {
      orderId: response.orderID,
      tokenId,
      side,
      price,
      size,
      status: response.status as PolymarketOrder['status'],
      createdAt: Date.now(),
    };

    this.activeOrders.set(order.orderId, order);
    this.emit('order:placed', order);

    return order;
  }

  /**
   * Place a market order
   */
  async placeMarketOrder(
    tokenId: string,
    amount: number,
    side: 'BUY' | 'SELL',
    orderType: OrderType.FOK | OrderType.FAK = OrderType.FOK,
  ): Promise<PolymarketOrder> {
    if (!this.clobClient.isReady()) {
      throw new Error('Polymarket client not authenticated');
    }

    // Validate market order parameters
    if (amount <= 0) throw new Error(`Invalid amount ${amount}: must be > 0`);
    if (isNaN(amount)) throw new Error('Amount is NaN');

    // Slippage warning for market orders: log spread check
    const tick = this.latestTicks.get(tokenId);
    if (tick && tick.spread > 0.01) {
      logger.warn(`[Polymarket] Wide spread ${(tick.spread * 100).toFixed(1)}% on market order for ${tokenId}`);
    }

    const response = await withTimeout(
      this.clobClient.createAndPostMarketOrder(tokenId, amount, side, orderType),
      API_TIMEOUT_MS,
      'placeMarketOrder',
    );

    const order: PolymarketOrder = {
      orderId: response.orderID,
      tokenId,
      side,
      price: 0, // Market order
      size: amount,
      status: response.status as PolymarketOrder['status'],
      createdAt: Date.now(),
    };

    this.activeOrders.set(order.orderId, order);
    this.emit('order:placed', order);

    return order;
  }

  /**
   * Cancel an order
   */
  async cancelOrder(orderId: string): Promise<void> {
    if (!this.clobClient.isReady()) {
      throw new Error('Polymarket client not authenticated');
    }

    await this.clobClient.cancelOrder(orderId);
    const order = this.activeOrders.get(orderId);
    if (order) {
      order.status = 'cancelled';
      this.emit('order:cancelled', order);
      this.activeOrders.delete(orderId);
    }
  }

  /**
   * Cancel all orders
   */
  async cancelAllOrders(): Promise<void> {
    if (!this.clobClient.isReady()) {
      throw new Error('Polymarket client not authenticated');
    }

    await this.clobClient.cancelAll();

    // Emit cancelled events for all active orders
    for (const order of this.activeOrders.values()) {
      order.status = 'cancelled';
      this.emit('order:cancelled', order);
    }
    this.activeOrders.clear();
  }

  /**
   * Get open orders
   */
  async getOpenOrders(market?: string): Promise<PolymarketOrder[]> {
    if (!this.clobClient.isReady()) {
      return Array.from(this.activeOrders.values());
    }

    const orders = await this.clobClient.getOpenOrders(
      market ? { market } : undefined
    );

    return orders.map(o => ({
      orderId: o.id,
      tokenId: o.asset_id,
      side: o.side as 'BUY' | 'SELL',
      price: typeof o.price === 'string' ? parseFloat(o.price) : o.price,
      size: typeof o.original_size === 'string' ? parseFloat(o.original_size) : o.original_size,
      status: o.status as PolymarketOrder['status'],
      createdAt: new Date(o.created_at).getTime(),
    }));
  }

  /**
   * Get trade history
   */
  async getTradeHistory(market?: string, limit = 100): Promise<any[]> {
    if (!this.clobClient.isReady()) {
      return [];
    }

    return this.clobClient.getTrades(market ? { market } : undefined);
  }

  /**
   * Get orderbook for a token
   */
  async getOrderBook(tokenId: string): Promise<{
    bids: Array<{ price: number; size: number }>;
    asks: Array<{ price: number; size: number }>;
  }> {
    const book = await this.clobClient.getOrderBook(tokenId);
    return {
      bids: book.bids.map((b: { price: string; size: string }) => ({
        price: parseFloat(b.price),
        size: parseFloat(b.size),
      })),
      asks: book.asks.map((a: { price: string; size: string }) => ({
        price: parseFloat(a.price),
        size: parseFloat(a.size),
      })),
    };
  }

  /**
   * Get best bid/ask for a token
   */
  getBestBidAsk(tokenId: string): { bid: number; ask: number; spread: number } | null {
    const tick = this.latestTicks.get(tokenId);
    if (!tick) return null;
    return { bid: tick.bid, ask: tick.ask, spread: tick.spread };
  }

  /**
   * Check orderbook depth — verify enough liquidity for order size
   * Returns estimated fill price and slippage for given size
   */
  async checkDepth(tokenId: string, size: number, side: 'BUY' | 'SELL'): Promise<{
    hasSufficientDepth: boolean;
    estimatedFillPrice: number;
    estimatedSlippageBps: number;
    availableSize: number;
  }> {
    const book = await this.getOrderBook(tokenId);
    const levels = side === 'BUY' ? book.asks : book.bids;

    let filled = 0;
    let cost = 0;

    for (const level of levels) {
      const fillQty = Math.min(level.size, size - filled);
      cost += fillQty * level.price;
      filled += fillQty;
      if (filled >= size) break;
    }

    const midTick = this.latestTicks.get(tokenId);
    const midPrice = midTick ? (midTick.bid + midTick.ask) / 2 : (levels[0]?.price || 0);
    const avgFillPrice = filled > 0 ? cost / filled : 0;
    const slippageBps = midPrice > 0 ? Math.abs(avgFillPrice - midPrice) / midPrice * 10000 : 0;

    return {
      hasSufficientDepth: filled >= size,
      estimatedFillPrice: avgFillPrice,
      estimatedSlippageBps: slippageBps,
      availableSize: filled,
    };
  }

  /**
   * Get latest tick for a token
   */
  getLatestTick(tokenId: string): PolymarketTick | null {
    return this.latestTicks.get(tokenId) || null;
  }

  /**
   * Search markets via Gamma API
   */
  async searchMarkets(query: string, limit = 50) {
    return this.gammaClient.search(query, limit);
  }

  /**
   * Find crypto short-duration markets
   */
  async findCryptoShortMarkets() {
    return this.gammaClient.findCryptoShortMarkets();
  }

  /**
   * Get balance and allowance
   */
  async getBalanceAllowance(assetType: 'COLLATERAL' | 'CONDITIONAL' = 'COLLATERAL') {
    if (!this.clobClient.isReady()) {
      throw new Error('Polymarket client not authenticated');
    }
    return this.clobClient.getBalanceAllowance({ asset_type: assetType });
  }

  /**
   * Purge stale orders from activeOrders map (older than maxAgeMs)
   * Call periodically to prevent memory leak from unfilled/expired orders
   */
  purgeStaleOrders(maxAgeMs: number = 3600000): number {
    const now = Date.now();
    let purged = 0;
    for (const [id, order] of this.activeOrders) {
      if (now - order.createdAt > maxAgeMs) {
        this.activeOrders.delete(id);
        purged++;
      }
    }
    if (purged > 0) {
      logger.info(`[Polymarket] Purged ${purged} stale orders (older than ${maxAgeMs / 1000}s)`);
    }
    return purged;
  }

  /**
   * Check if client is ready for trading
   */
  isReady(): boolean {
    return this.clobClient.isReady();
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.running && this.wsClient?.isConnected() === true;
  }

  /**
   * Get active orders count
   */
  getActiveOrdersCount(): number {
    return this.activeOrders.size;
  }

  private handleBestBidAsk(event: BestBidAskEvent): void {
    const bid = parseFloat(event.best_bid);
    const ask = parseFloat(event.best_ask);
    const spread = parseFloat(event.spread);

    // NaN guard: reject corrupted price data instead of propagating to strategies
    if (isNaN(bid) || isNaN(ask)) {
      logger.warn(`[Polymarket] NaN price for ${event.asset_id}: bid=${event.best_bid} ask=${event.best_ask}`);
      return;
    }

    const tick: PolymarketTick = {
      exchange: 'polymarket',
      symbol: event.market,
      tokenId: event.asset_id,
      bid,
      ask,
      spread: isNaN(spread) ? ask - bid : spread,
      timestamp: Date.now(),
    };

    this.latestTicks.set(tick.tokenId, tick);
    this.emit('tick', tick);
  }

  private startHeartbeat(): void {
    if (!this.config.autoHeartbeat) return;

    // Send heartbeat every 10 seconds (Polymarket requires < 10s interval)
    this.heartbeatTimer = setInterval(async () => {
      if (this.running && this.clobClient.isReady()) {
        try {
          await this.clobClient.sendHeartbeat();
        } catch (err) {
          logger.warn('[Polymarket] Heartbeat failed:', err instanceof Error ? err.message : String(err));
        }
      }
    }, 8000); // 8s interval for safety margin
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}

export { OrderType, Side };
