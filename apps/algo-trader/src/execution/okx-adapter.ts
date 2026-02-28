/**
 * OkxAdapter — OKX-specific exchange adapter.
 * Extends ExchangeClient with OKX fee tiers, passphrase support, instId format.
 */

import { ExchangeClient } from './ExchangeClient';

/** OKX spot maker/taker fee schedule */
const OKX_FEE_TIERS = {
  default: { maker: 0.001, taker: 0.0015 },
} as const;

export interface OkxAdapterConfig {
  apiKey?: string;
  secret?: string;
  /** OKX requires passphrase for authenticated API calls */
  passphrase?: string;
}

export class OkxAdapter extends ExchangeClient {
  readonly exchangeId = 'okx' as const;
  private readonly feeRate: { maker: number; taker: number };

  constructor(config: OkxAdapterConfig = {}) {
    super('okx', config.apiKey, config.secret);
    this.feeRate = { ...OKX_FEE_TIERS.default };
  }

  /** OKX-specific fee rates */
  getFeeRate(): { maker: number; taker: number } {
    return { ...this.feeRate };
  }

  /** Taker fee used for arb cost estimation */
  getTakerFee(): number {
    return this.feeRate.taker;
  }
}
