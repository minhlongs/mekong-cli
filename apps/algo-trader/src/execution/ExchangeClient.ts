/**
 * Exchange Client
 *
 * Abstracts interaction with cryptocurrency exchanges using CCXT.
 * Provides a unified interface for trading operations across different exchanges.
 */

import { IOrder, IBalance } from '../interfaces/IExchange';
import { logger } from '../utils/logger';

export interface IExchangeConfig {
  apiKey: string;
  secret: string;
  password?: string; // Some exchanges require this
  uid?: string;     // Some exchanges require this
  sandbox?: boolean;
}

export class ExchangeClient {
  private exchange: any; // CCXT exchange instance // CCXT exchange instance
  private exchangeId: string;
  private config: IExchangeConfig;

  constructor(exchangeId: string, config: IExchangeConfig) {
    this.exchangeId = exchangeId;
    this.config = config;

    // Dynamically import CCXT to avoid bundling issues
    const ccxt = require('ccxt');

    // Initialize the exchange with provided config
    this.exchange = new ccxt[exchangeId]({
      apiKey: config.apiKey,
      secret: config.secret,
      password: config.password,
      uid: config.uid,
      sandbox: config.sandbox || false,
      enableRateLimit: true, // Essential for API compliance
    });
  }

  /**
   * Initialize the exchange client (currently just verifies connection)
   */
  async initialize(): Promise<void> {
    try {
      await this.exchange.loadMarkets();
      logger.info(`Connected to ${this.exchangeId} exchange`);
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : 'Unknown error';
      throw new Error(`Failed to initialize ${this.exchangeId} exchange: ${msg}`);
    }
  }

  /**
   * Close the exchange connection
   */
  async close(): Promise<void> {
    // CCXT doesn't require explicit closing in most cases
    // But we can set exchange to null to clean up
    this.exchange = null;
  }

  /**
   * Get ticker for a symbol
   */
  async fetchTicker(symbol: string): Promise<any> {
    try {
      return await this.exchange.fetchTicker(symbol);
    } catch (error: unknown) {
      if (error instanceof Error) {
        throw new Error(`Failed to fetch ticker for ${symbol} on ${this.exchangeId}: ${error.message}`);
      } else {
        throw new Error(`Failed to fetch ticker for ${symbol} on ${this.exchangeId}: Unknown error`);
      }
    }
  }

  /**
   * Get order book for a symbol
   */
  async fetchOrderBook(symbol: string, limit?: number) {
    try {
      return await this.exchange.fetchOrderBook(symbol, limit);
    } catch (error: unknown) {
      if (error instanceof Error) {
        throw new Error(`Failed to fetch order book for ${symbol} on ${this.exchangeId}: ${error.message}`);
      } else {
        throw new Error(`Failed to fetch order book for ${symbol} on ${this.exchangeId}: Unknown error`);
      }
    }
  }

  /**
   * Get balance for all currencies
   */
  async getBalance(): Promise<Record<string, IBalance>> {
    try {
      const rawBalance = await this.exchange.fetchBalance();
      // Transform the raw balance to match our IBalance interface
      const transformedBalance: Record<string, IBalance> = {};

      for (const [currency, amount] of Object.entries(rawBalance.total || rawBalance)) {
        transformedBalance[currency] = {
          currency: currency as string,
          free: rawBalance.free?.[currency as string] || 0,
          used: rawBalance.used?.[currency as string] || 0,
          total: rawBalance.total?.[currency as string] || Number(amount) || 0,
        };
      }

      return transformedBalance;
    } catch (error: unknown) {
      if (error instanceof Error) {
        throw new Error(`Failed to fetch balance from ${this.exchangeId}: ${error.message}`);
      } else {
        throw new Error(`Failed to fetch balance from ${this.exchangeId}: Unknown error`);
      }
    }
  }

  /**
   * Place a market order
   */
  async marketOrder(side: 'buy' | 'sell', symbol: string, amount: number, params: any = {}): Promise<IOrder> {
    try {
      const order = await this.exchange.createMarketOrder(
        symbol,
        side,
        amount,
        undefined, // price not needed for market orders
        params
      );

      // Normalize the order response to match our IOrder interface
      return {
        id: order.id || `order_${Date.now()}`,
        symbol: order.symbol || symbol,
        side: side,
        amount: order.amount || amount,
        price: order.price || order.average || order.lastTradePrice || 0,
        status: (order.status as 'open' | 'closed' | 'canceled') || 'closed',
        timestamp: order.timestamp || Date.now(),
      };
    } catch (error: unknown) {
      if (error instanceof Error) {
        throw new Error(`Failed to place ${side} market order for ${symbol} on ${this.exchangeId}: ${error.message}`);
      } else {
        throw new Error(`Failed to place ${side} market order for ${symbol} on ${this.exchangeId}: Unknown error`);
      }
    }
  }

  /**
   * Place a limit order
   */
  async limitOrder(side: 'buy' | 'sell', symbol: string, amount: number, price: number, params: any = {}): Promise<IOrder> {
    try {
      const order = await this.exchange.createLimitOrder(
        symbol,
        side,
        amount,
        price,
        params
      );

      // Normalize the order response to match our IOrder interface
      return {
        id: order.id || `order_${Date.now()}`,
        symbol: order.symbol || symbol,
        side: side,
        amount: order.amount || amount,
        price: order.price || price,
        status: (order.status as 'open' | 'closed' | 'canceled') || 'open',
        timestamp: order.timestamp || Date.now(),
      };
    } catch (error: unknown) {
      if (error instanceof Error) {
        throw new Error(`Failed to place ${side} limit order for ${symbol} at $${price} on ${this.exchangeId}: ${error.message}`);
      } else {
        throw new Error(`Failed to place ${side} limit order for ${symbol} at $${price} on ${this.exchangeId}: Unknown error`);
      }
    }
  }

  /**
   * Cancel an order
   */
  async cancelOrder(orderId: string, symbol: string, params: any = {}): Promise<IOrder> {
    try {
      const order = await this.exchange.cancelOrder(orderId, symbol, params);

      return {
        id: order.id || orderId,
        symbol: order.symbol || symbol,
        side: order.side as 'buy' | 'sell',
        amount: order.amount || 0,
        price: order.price || 0,
        status: 'canceled',
        timestamp: order.timestamp || Date.now(),
      };
    } catch (error: unknown) {
      if (error instanceof Error) {
        throw new Error(`Failed to cancel order ${orderId} on ${this.exchangeId}: ${error.message}`);
      } else {
        throw new Error(`Failed to cancel order ${orderId} on ${this.exchangeId}: Unknown error`);
      }
    }
  }

  /**
   * Fetch an order by ID
   */
  async fetchOrder(orderId: string, symbol: string, params: any = {}): Promise<IOrder> {
    try {
      const order = await this.exchange.fetchOrder(orderId, symbol, params);

      return {
        id: order.id || orderId,
        symbol: order.symbol || symbol,
        side: order.side as 'buy' | 'sell',
        amount: order.amount || 0,
        price: order.price || 0,
        status: (order.status as 'open' | 'closed' | 'canceled') || 'open',
        timestamp: order.timestamp || Date.now(),
      };
    } catch (error: unknown) {
      if (error instanceof Error) {
        throw new Error(`Failed to fetch order ${orderId} on ${this.exchangeId}: ${error.message}`);
      } else {
        throw new Error(`Failed to fetch order ${orderId} on ${this.exchangeId}: Unknown error`);
      }
    }
  }

  /**
   * Get all open orders
   */
  async fetchOpenOrders(symbol?: string, params: any = {}): Promise<IOrder[]> {
    try {
      const orders = await this.exchange.fetchOpenOrders(symbol, undefined, undefined, params);

      return orders.map((order: any) => ({
        id: order.id || `order_${Date.now()}`,
        symbol: order.symbol || symbol || '',
        side: order.side as 'buy' | 'sell',
        amount: order.amount || 0,
        price: order.price || 0,
        status: (order.status as 'open' | 'closed' | 'canceled') || 'open',
        timestamp: order.timestamp || Date.now(),
      }));
    } catch (error: unknown) {
      if (error instanceof Error) {
        throw new Error(`Failed to fetch open orders on ${this.exchangeId}: ${error.message}`);
      } else {
        throw new Error(`Failed to fetch open orders on ${this.exchangeId}: Unknown error`);
      }
    }
  }

  /**
   * Get recent trades
   */
  async fetchMyTrades(symbol?: string, params: any = {}): Promise<any[]> {
    try {
      return await this.exchange.fetchMyTrades(symbol, undefined, undefined, params);
    } catch (error: unknown) {
      if (error instanceof Error) {
        throw new Error(`Failed to fetch trades from ${this.exchangeId}: ${error.message}`);
      } else {
        throw new Error(`Failed to fetch trades from ${this.exchangeId}: Unknown error`);
      }
    }
  }

  /**
   * Check if the exchange is online
   */
  async checkHealth(): Promise<boolean> {
    try {
      await this.exchange.fetchStatus();
      return this.exchange.has?.fetchTicker === true && this.exchange.healthCheck !== false;
    } catch {
      return false;
    }
  }

  /**
   * Get exchange ID
   */
  getExchangeId(): string {
    return this.exchangeId;
  }
}