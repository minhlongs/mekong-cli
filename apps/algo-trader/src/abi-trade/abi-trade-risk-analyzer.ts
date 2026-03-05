/**
 * AbiTrade Risk Analyzer — Comprehensive risk assessment for arbitrage opportunities
 * Evaluates multiple risk factors to ensure safe and profitable trading
 */

import { RiskFactor } from './abi-trade-types';

export interface RiskConfig {
  volatilityThreshold: number;     // Threshold for volatility risk (0.02 = 2%)
  liquidityThreshold: number;      // Threshold for liquidity risk (in USD volume)
  volumeThreshold: number;         // Minimum trading volume
  maxPositionSize: number;         // Maximum position size in USD
  volatilityWindow: number;        // Window size for volatility calculation
  correlationRiskThreshold: number; // Threshold for correlation risk
  latencyRiskThreshold: number;    // Threshold for latency risk (in ms)
}

export interface ExchangeRiskProfile {
  exchangeId: string;
  volatilityScore: number;
  liquidityScore: number;
  volumeScore: number;
  latencyScore: number;
  overallRiskScore: number;
}

export class AbiTradeRiskAnalyzer {
  private config: RiskConfig;

  constructor(config?: Partial<RiskConfig>) {
    this.config = this.mergeDefaultConfig(config);
  }

  private mergeDefaultConfig(config?: Partial<RiskConfig>): RiskConfig {
    const defaults: RiskConfig = {
      volatilityThreshold: 0.02, // 2% daily volatility threshold
      liquidityThreshold: 100000, // $100K minimum liquidity
      volumeThreshold: 10000, // $10K minimum volume
      maxPositionSize: 5000, // $5K max position
      volatilityWindow: 20, // 20 periods for volatility calc
      correlationRiskThreshold: 0.9, // 90% correlation = high risk
      latencyRiskThreshold: 1000, // 1 second max latency for arbitrage
    };

    return { ...defaults, ...config };
  }

  /**
   * Analyze risk factors for a given symbol across exchanges
   */
  analyzeRiskFactors(symbol: string, priceData: any[]): RiskFactor[] {
    const riskFactors: RiskFactor[] = [];

    // Analyze volatility risk
    riskFactors.push(...this.analyzeVolatilityRisk(symbol, priceData));

    // Analyze liquidity risk
    riskFactors.push(...this.analyzeLiquidityRisk(symbol, priceData));

    // Analyze volume risk
    riskFactors.push(...this.analyzeVolumeRisk(symbol, priceData));

    // Analyze latency risk
    riskFactors.push(...this.analyzeLatencyRisk(symbol, priceData));

    // Analyze correlation risk
    riskFactors.push(...this.analyzeCorrelationRisk(symbol, priceData));

    return riskFactors;
  }

  /**
   * Analyze volatility risk for each exchange
   */
  private analyzeVolatilityRisk(symbol: string, priceData: any[]): RiskFactor[] {
    const riskFactors: RiskFactor[] = [];

    for (const data of priceData) {
      const exchange = data.exchange;
      const prices = data.prices || []; // Assuming price history is available

      if (prices.length >= this.config.volatilityWindow) {
        // Calculate rolling volatility (standard deviation of returns)
        const returns = this.calculateReturns(prices.slice(-this.config.volatilityWindow));
        const volatility = this.calculateStdDev(returns);

        const severity = this.getSeverityFromValue(volatility, this.config.volatilityThreshold);

        riskFactors.push({
          type: 'volatility',
          severity,
          value: volatility,
          threshold: this.config.volatilityThreshold,
          description: `${exchange} volatility for ${symbol}: ${volatility.toFixed(4)}, threshold: ${this.config.volatilityThreshold}`
        });
      }
    }

    return riskFactors;
  }

  /**
   * Analyze liquidity risk
   */
  private analyzeLiquidityRisk(symbol: string, priceData: any[]): RiskFactor[] {
    const riskFactors: RiskFactor[] = [];

    for (const data of priceData) {
      const exchange = data.exchange;
      const orderBook = data.orderBook;

      if (orderBook && orderBook.bids && orderBook.asks) {
        // Calculate available liquidity in the order book
        const bidVolume = orderBook.bids.slice(0, 5).reduce((sum: number, [price, amount]: [number, number]) => sum + (price * amount), 0);
        const askVolume = orderBook.asks.slice(0, 5).reduce((sum: number, [price, amount]: [number, number]) => sum + (price * amount), 0);
        const availableLiquidity = Math.min(bidVolume, askVolume);

        const severity = availableLiquidity < this.config.liquidityThreshold ? 'high' : 'low';

        riskFactors.push({
          type: 'liquidity',
          severity,
          value: availableLiquidity,
          threshold: this.config.liquidityThreshold,
          description: `${exchange} liquidity for ${symbol}: $${availableLiquidity.toFixed(2)}, threshold: $${this.config.liquidityThreshold}`
        });
      }
    }

    return riskFactors;
  }

  /**
   * Analyze volume risk
   */
  private analyzeVolumeRisk(symbol: string, priceData: any[]): RiskFactor[] {
    const riskFactors: RiskFactor[] = [];

    for (const data of priceData) {
      const exchange = data.exchange;
      const ticker = data.ticker;

      // Use quoteVolume if available (trading volume in USD/quote currency)
      const volume = ticker.quoteVolume || ticker.baseVolume || ticker.volume || 0;

      const severity = volume < this.config.volumeThreshold ? 'high' : 'low';

      riskFactors.push({
        type: 'volume',
        severity,
        value: volume,
        threshold: this.config.volumeThreshold,
        description: `${exchange} volume for ${symbol}: $${volume.toFixed(2)}, threshold: $${this.config.volumeThreshold}`
      });
    }

    return riskFactors;
  }

  /**
   * Analyze latency risk between exchanges
   */
  private analyzeLatencyRisk(symbol: string, priceData: any[]): RiskFactor[] {
    const riskFactors: RiskFactor[] = [];

    // Get latency data for exchanges
    for (const data of priceData) {
      const exchange = data.exchange;
      const latency = data.latency || 0;

      const severity = latency > this.config.latencyRiskThreshold ? 'high' : 'low';

      riskFactors.push({
        type: 'latency',
        severity,
        value: latency,
        threshold: this.config.latencyRiskThreshold,
        description: `${exchange} latency for ${symbol}: ${latency}ms, threshold: ${this.config.latencyRiskThreshold}ms`
      });
    }

    return riskFactors;
  }

  /**
   * Analyze correlation risk between exchanges
   */
  private analyzeCorrelationRisk(symbol: string, priceData: any[]): RiskFactor[] {
    const riskFactors: RiskFactor[] = [];

    // For correlation risk, we need to compare prices between exchanges
    const exchangePrices: { [exchange: string]: number } = {};
    for (const data of priceData) {
      exchangePrices[data.exchange] = data.ticker.last;
    }

    const exchanges = Object.keys(exchangePrices);

    // Compare all pairs of exchanges
    for (let i = 0; i < exchanges.length; i++) {
      for (let j = i + 1; j < exchanges.length; j++) {
        const ex1 = exchanges[i];
        const ex2 = exchanges[j];
        const price1 = exchangePrices[ex1];
        const price2 = exchangePrices[ex2];

        // Calculate price difference as percentage
        const priceDiffPercent = Math.abs((price1 - price2) / ((price1 + price2) / 2)) * 100;

        // If prices are too similar (high correlation), it might indicate lack of arbitrage opportunity
        const severity = priceDiffPercent < 0.1 ? 'high' : 'low'; // Less than 0.1% difference

        riskFactors.push({
          type: 'correlation',
          severity,
          value: priceDiffPercent,
          threshold: 0.1,
          description: `Correlation risk between ${ex1} and ${ex2} for ${symbol}: ${priceDiffPercent.toFixed(3)}% price difference`
        });
      }
    }

    return riskFactors;
  }

  /**
   * Calculate returns from a series of prices
   */
  private calculateReturns(prices: number[]): number[] {
    const returns: number[] = [];

    for (let i = 1; i < prices.length; i++) {
      const returnVal = (prices[i] - prices[i - 1]) / prices[i - 1];
      returns.push(returnVal);
    }

    return returns;
  }

  /**
   * Calculate standard deviation
   */
  private calculateStdDev(values: number[]): number {
    if (values.length === 0) return 0;

    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
    const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / values.length;

    return Math.sqrt(variance);
  }

  /**
   * Determine severity based on value and threshold
   */
  private getSeverityFromValue(value: number, threshold: number): 'low' | 'medium' | 'high' | 'critical' {
    if (value <= threshold * 0.5) {
      return 'low';
    } else if (value <= threshold) {
      return 'medium';
    } else if (value <= threshold * 2) {
      return 'high';
    } else {
      return 'critical';
    }
  }

  /**
   * Calculate overall risk profile for an exchange
   */
  getExchangeRiskProfile(exchangeId: string, riskFactors: RiskFactor[]): ExchangeRiskProfile {
    const exchangeFactors = riskFactors.filter(factor => factor.description.includes(exchangeId));

    let volatilityScore = 0;
    let liquidityScore = 0;
    let volumeScore = 0;
    let latencyScore = 0;

    let factorCount = 0;

    for (const factor of exchangeFactors) {
      factorCount++;
      switch (factor.type) {
        case 'volatility':
          volatilityScore = this.severityToScore(factor.severity);
          break;
        case 'liquidity':
          liquidityScore = this.severityToScore(factor.severity);
          break;
        case 'volume':
          volumeScore = this.severityToScore(factor.severity);
          break;
        case 'latency':
          latencyScore = this.severityToScore(factor.severity);
          break;
      }
    }

    // Calculate average risk score (0-100, lower is better)
    const avgRiskScore = factorCount > 0
      ? (volatilityScore + liquidityScore + volumeScore + latencyScore) / factorCount
      : 0;

    return {
      exchangeId,
      volatilityScore,
      liquidityScore,
      volumeScore,
      latencyScore,
      overallRiskScore: avgRiskScore
    };
  }

  /**
   * Convert severity to numeric score (0-100, where lower is better)
   */
  private severityToScore(severity: 'low' | 'medium' | 'high' | 'critical'): number {
    switch (severity) {
      case 'low': return 20;
      case 'medium': return 40;
      case 'high': return 70;
      case 'critical': return 95;
    }
  }

  /**
   * Get risk summary for all exchanges
   */
  getRiskSummary(riskFactors: RiskFactor[]): { [exchangeId: string]: ExchangeRiskProfile } {
    const exchangeIds = [...new Set(riskFactors.map(f =>
      f.description.split(' ')[0] // Get exchange ID from description
    ))];

    const summary: { [exchangeId: string]: ExchangeRiskProfile } = {};

    for (const exchangeId of exchangeIds) {
      summary[exchangeId] = this.getExchangeRiskProfile(exchangeId, riskFactors);
    }

    return summary;
  }

  /**
   * Assess if a position size is safe given the risk factors
   */
  isPositionSafe(positionSize: number, riskFactors: RiskFactor[]): boolean {
    // Check if position size is within limits
    if (positionSize > this.config.maxPositionSize) {
      return false;
    }

    // Check if there are critical risk factors
    const criticalRisks = riskFactors.filter(factor => factor.severity === 'critical');
    return criticalRisks.length === 0;
  }
}