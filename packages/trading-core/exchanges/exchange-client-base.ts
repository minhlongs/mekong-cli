/**
 * ExchangeClientBase — CCXT wrapper implementing IExchange interface.
 * Provides connect, fetchTicker, createMarketOrder, fetchBalance, fetchOrderBook
 * with retry logic and rate limit handling.
 *
 * Used as base class for exchange-specific adapters (Binance, OKX, Bybit).
 * Requires ccxt as peer dependency at runtime.
 */

import { IExchange, IOrder, IBalance, IOrderBook } from '../interfaces/exchange-types';

interface CcxtMarketLimits {
  limits?: {
    amount?: { min?: number };
    cost?: { min?: number };
  };
}

interface CcxtOrderResult {
  id: string;
  symbol: string;
  side: string;
  amount: number;
  average?: number;
  price?: number;
  status: string;
  timestamp: number;
}

interface CcxtOrderBookResult {
  bids?: number[][];
  asks?: number[][];
  timestamp?: number;
}

interface CcxtBalanceResult {
  total?: Record<string, number>;
  free?: Record<string, number>;
  used?: Record<string, number>;
}

interface CcxtExchangeInstance {
  loadMarkets: () => Promise<void>;
  fetchTicker: (symbol: string) => Promise<{ last?: number }>;
  amountToPrecision: (symbol: string, amount: number) => string;
  markets?: Record<string, CcxtMarketLimits | undefined>;
  createOrder: (symbol: string, type: string, side: string, amount: number) => Promise<CcxtOrderResult>;
  fetchOrderBook: (symbol: string, limit?: number) => Promise<CcxtOrderBookResult>;
  fetchBalance: () => Promise<CcxtBalanceResult>;
}

export class ExchangeClientBase implements IExchange {
  name: string;
  protected exchange: unknown;

  constructor(exchangeId: string, apiKey?: string, secret?: string) {
    this.name = exchangeId;

    // Dynamic CCXT exchange instantiation (peer dependency)
    const ccxtLib = require('ccxt') as Record<string, (new (opts: Record<string, unknown>) => unknown) | undefined>;
    const ExchangeClass = ccxtLib[exchangeId];
    if (!ExchangeClass) {
      throw new Error(`Exchange ${exchangeId} not found in CCXT`);
    }

    this.exchange = new ExchangeClass({
      apiKey,
      secret,
      enableRateLimit: true,
      timeout: 30000,
      options: { defaultType: 'spot' },
    });
  }

  private get ccxtExchange(): CcxtExchangeInstance {
    return this.exchange as CcxtExchangeInstance;
  }

  async connect(): Promise<void> {
    await this.ccxtExchange.loadMarkets();
  }

  protected async retry<T>(fn: () => Promise<T>, retries = 3, delay = 1000): Promise<T> {
    try {
      return await fn();
    } catch (error) {
      if (retries <= 0) throw error;
      const isRateLimit = error instanceof Error && (
        error.message.includes('429') || error.message.includes('RateLimitExceeded')
      );
      const backoff = isRateLimit ? delay * 2 : delay;
      await new Promise(resolve => setTimeout(resolve, backoff));
      return this.retry(fn, retries - 1, backoff);
    }
  }

  async fetchTicker(symbol: string): Promise<number> {
    const ex = this.ccxtExchange;
    const ticker = await this.retry(() => ex.fetchTicker(symbol));
    return ticker.last || 0;
  }

  async createMarketOrder(symbol: string, side: 'buy' | 'sell', amount: number): Promise<IOrder> {
    const ex = this.ccxtExchange;
    const preciseAmountStr = ex.amountToPrecision(symbol, amount);
    const preciseAmount = parseFloat(preciseAmountStr);

    const market = ex.markets?.[symbol];
    if (market) {
      const minAmount = market.limits?.amount?.min;
      const minCost = market.limits?.cost?.min;
      if (minAmount && preciseAmount < minAmount) {
        throw new Error(`Order amount ${preciseAmount} below exchange minimum ${minAmount} for ${symbol}`);
      }
      if (minCost) {
        const ticker = await this.fetchTicker(symbol);
        const estimatedCost = preciseAmount * ticker;
        if (estimatedCost < minCost) {
          throw new Error(`Order cost ~$${estimatedCost.toFixed(2)} below exchange minimum $${minCost} for ${symbol}`);
        }
      }
    }

    const order = await this.retry(() => ex.createOrder(symbol, 'market', side, preciseAmount));
    const filledPrice = order.average || order.price || 0;

    return {
      id: order.id,
      symbol: order.symbol,
      side: order.side as 'buy' | 'sell',
      amount: order.amount,
      price: filledPrice,
      status: order.status === 'open' ? 'open' : 'closed',
      timestamp: order.timestamp,
    };
  }

  async fetchOrderBook(symbol: string, limit = 20): Promise<IOrderBook> {
    const ex = this.ccxtExchange;
    const book = await this.retry(() => ex.fetchOrderBook(symbol, limit));
    return {
      symbol,
      bids: (book.bids || []).map((entry: number[]) => ({ price: Number(entry[0]) || 0, amount: Number(entry[1]) || 0 })),
      asks: (book.asks || []).map((entry: number[]) => ({ price: Number(entry[0]) || 0, amount: Number(entry[1]) || 0 })),
      timestamp: book.timestamp || Date.now(),
    };
  }

  async fetchBalance(): Promise<Record<string, IBalance>> {
    const ex = this.ccxtExchange;
    const balance = await this.retry(() => ex.fetchBalance());
    const result: Record<string, IBalance> = {};

    const total = balance.total;
    const free = balance.free;
    const used = balance.used;

    if (total) {
      for (const [currency, amount] of Object.entries(total)) {
        if (amount > 0) {
          result[currency] = {
            currency,
            free: free?.[currency] || 0,
            used: used?.[currency] || 0,
            total: amount,
          };
        }
      }
    }
    return result;
  }
}
