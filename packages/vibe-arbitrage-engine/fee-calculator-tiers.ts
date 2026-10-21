/**
 * FeeCalculator types and default exchange fee schedules.
 */

export interface FeeTier {
  level: string;            // e.g., "VIP0", "Regular", "VIP1"
  makerRate: number;        // Maker fee rate (e.g., 0.001 = 0.1%)
  takerRate: number;        // Taker fee rate (e.g., 0.001 = 0.1%)
  minVolume30d: number;     // Min 30-day volume to qualify (USD)
}

export interface ExchangeFeeSchedule {
  exchange: string;
  tiers: FeeTier[];
  withdrawalFees: Map<string, number>;  // currency → flat fee
}

export interface FeeBreakdown {
  exchange: string;
  side: 'buy' | 'sell';
  orderType: 'maker' | 'taker';
  rate: number;
  feeUsd: number;
  feeBase: number;          // Fee in base currency
}

export interface ArbitrageFeeReport {
  buyFee: FeeBreakdown;
  sellFee: FeeBreakdown;
  totalFeesUsd: number;
  withdrawalFeeUsd: number;  // If transferring between exchanges
  totalCostUsd: number;      // Fees + withdrawal
  breakEvenSpreadPercent: number;  // Min spread needed to cover all costs
}

export const DEFAULT_FEE_SCHEDULES: ExchangeFeeSchedule[] = [
  {
    exchange: 'binance',
    tiers: [
      { level: 'Regular', makerRate: 0.001, takerRate: 0.001, minVolume30d: 0 },
      { level: 'VIP1', makerRate: 0.0009, takerRate: 0.001, minVolume30d: 1000000 },
      { level: 'VIP2', makerRate: 0.0008, takerRate: 0.001, minVolume30d: 5000000 },
      { level: 'VIP3', makerRate: 0.00042, takerRate: 0.0006, minVolume30d: 20000000 },
    ],
    withdrawalFees: new Map([['BTC', 0.0000046], ['ETH', 0.00054], ['USDT', 1]]),
  },
  {
    exchange: 'okx',
    tiers: [
      { level: 'Regular', makerRate: 0.0008, takerRate: 0.001, minVolume30d: 0 },
      { level: 'VIP1', makerRate: 0.0006, takerRate: 0.0009, minVolume30d: 5000000 },
      { level: 'VIP2', makerRate: 0.0005, takerRate: 0.0007, minVolume30d: 10000000 },
      { level: 'VIP3', makerRate: 0.00035, takerRate: 0.0005, minVolume30d: 20000000 },
    ],
    withdrawalFees: new Map([['BTC', 0.0001], ['ETH', 0.0014], ['USDT', 1]]),
  },
  {
    exchange: 'bybit',
    tiers: [
      { level: 'Regular', makerRate: 0.001, takerRate: 0.001, minVolume30d: 0 },
      { level: 'VIP1', makerRate: 0.0006, takerRate: 0.0008, minVolume30d: 1000000 },
      { level: 'VIP2', makerRate: 0.0004, takerRate: 0.0006, minVolume30d: 5000000 },
      { level: 'VIP3', makerRate: 0.0002, takerRate: 0.0004, minVolume30d: 25000000 },
    ],
    withdrawalFees: new Map([['BTC', 0.0002], ['ETH', 0.0012], ['USDT', 1]]),
  },
  {
    exchange: 'gateio',
    tiers: [
      { level: 'Regular', makerRate: 0.002, takerRate: 0.002, minVolume30d: 0 },
      { level: 'VIP1', makerRate: 0.00185, takerRate: 0.00195, minVolume30d: 1500000 },
      { level: 'VIP2', makerRate: 0.00175, takerRate: 0.00185, minVolume30d: 3000000 },
      { level: 'VIP3', makerRate: 0.0015, takerRate: 0.0016, minVolume30d: 6000000 },
    ],
    withdrawalFees: new Map([['BTC', 0.001], ['ETH', 0.0082], ['USDT', 4]]),
  },
];
