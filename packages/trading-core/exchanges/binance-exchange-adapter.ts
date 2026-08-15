/**
 * BinanceExchangeAdapter — Binance-specific exchange adapter.
 * Extends ExchangeClientBase with Binance fee tiers and BNB discount support.
 */

import { ExchangeClientBase } from './exchange-client-base';

const BINANCE_FEE_TIERS = {
  default: { maker: 0.001, taker: 0.001 },
  bnbDiscount: { maker: 0.00075, taker: 0.00075 },
} as const;

export interface BinanceAdapterConfig {
  apiKey?: string;
  secret?: string;
  /** Enable BNB fee discount (25% off when paying fees in BNB) */
  useBnbDiscount?: boolean;
  /** Recv window for timestamp tolerance (ms) */
  recvWindow?: number;
}

export class BinanceAdapter extends ExchangeClientBase {
  readonly exchangeId = 'binance' as const;
  private readonly feeRate: { maker: number; taker: number };

  constructor(config: BinanceAdapterConfig = {}) {
    super('binance', config.apiKey, config.secret);
    this.feeRate = config.useBnbDiscount
      ? BINANCE_FEE_TIERS.bnbDiscount
      : BINANCE_FEE_TIERS.default;
  }

  /** Binance-specific fee rates (accounts for BNB discount) */
  getFeeRate(): { maker: number; taker: number } {
    return { ...this.feeRate };
  }

  /** Taker fee used for arb cost estimation */
  getTakerFee(): number {
    return this.feeRate.taker;
  }
}
