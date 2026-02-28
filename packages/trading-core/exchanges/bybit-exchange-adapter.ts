/**
 * BybitExchangeAdapter — Bybit-specific exchange adapter.
 * Extends ExchangeClientBase with Bybit unified trading account and fee tiers.
 */

import { ExchangeClientBase } from './exchange-client-base';

const BYBIT_FEE_TIERS = {
  default: { maker: 0.001, taker: 0.001 },
} as const;

export interface BybitAdapterConfig {
  apiKey?: string;
  secret?: string;
}

export class BybitAdapter extends ExchangeClientBase {
  readonly exchangeId = 'bybit' as const;
  private readonly feeRate: { maker: number; taker: number };

  constructor(config: BybitAdapterConfig = {}) {
    super('bybit', config.apiKey, config.secret);
    this.feeRate = { ...BYBIT_FEE_TIERS.default };
  }

  /** Bybit-specific fee rates */
  getFeeRate(): { maker: number; taker: number } {
    return { ...this.feeRate };
  }

  /** Taker fee used for arb cost estimation */
  getTakerFee(): number {
    return this.feeRate.taker;
  }
}
