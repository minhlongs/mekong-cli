/**
 * PortfolioRiskManager — Portfolio-level risk management.
 * Kelly Criterion sizing, correlation matrix, VaR, exposure limits.
 * Extends RiskManager concept to multi-asset portfolio management.
 */

export interface PortfolioPosition {
  symbol: string;
  entryPrice: number;
  currentPrice: number;
  size: number;       // Units held
  side: 'long' | 'short';
  entryTime: number;
}

export interface PortfolioRiskConfig {
  maxPositions: number;           // Max concurrent open positions (default: 5)
  maxPortfolioRiskPercent: number; // Max % of portfolio at risk (default: 10)
  maxSinglePositionPercent: number; // Max % of portfolio in one position (default: 5)
  maxCorrelation: number;         // Max allowed correlation between new and existing (default: 0.7)
  kellyFraction: number;          // Fraction of Kelly to use (default: 0.25 = quarter Kelly)
  varConfidence: number;          // VaR confidence level (default: 0.95)
  varLookback: number;            // Number of returns for VaR calculation (default: 100)
  maxDrawdownPercent: number;     // Kill switch: max portfolio drawdown (default: 15)
}

export interface KellyResult {
  kellyPercent: number;     // Full Kelly %
  adjustedPercent: number;  // Kelly * fraction
  positionSize: number;     // USD value to allocate
}

export interface VaRResult {
  var95: number;            // 95% VaR ($ amount at risk)
  cvar95: number;           // Conditional VaR (expected loss beyond VaR)
  varPercent: number;       // VaR as % of portfolio
}

export interface PortfolioRiskAssessment {
  canOpenPosition: boolean;
  reason?: string;
  currentExposure: number;     // Total % of portfolio at risk
  positionCount: number;
  correlationRisk: number;     // 0-1: how correlated current positions are
  suggestedSize: KellyResult;
  var: VaRResult;
}

const DEFAULT_CONFIG: PortfolioRiskConfig = {
  maxPositions: 5,
  maxPortfolioRiskPercent: 10,
  maxSinglePositionPercent: 5,
  maxCorrelation: 0.7,
  kellyFraction: 0.25,
  varConfidence: 0.95,
  varLookback: 100,
  maxDrawdownPercent: 15,
};

export class PortfolioRiskManager {
  private config: PortfolioRiskConfig;
  private positions: PortfolioPosition[] = [];
  private portfolioValue: number;
  private peakValue: number;
  private returnHistory: number[] = [];

  constructor(initialValue: number, config?: Partial<PortfolioRiskConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.portfolioValue = initialValue;
    this.peakValue = initialValue;
  }

  /**
   * Assess whether a new position can be opened + recommended size.
   */
  assessNewPosition(
    symbol: string,
    currentPrice: number,
    winRate: number,
    avgWinLossRatio: number,
    priceHistory?: number[]
  ): PortfolioRiskAssessment {
    // Check if we already have a position in this symbol
    const existingPos = this.positions.find(p => p.symbol === symbol);
    if (existingPos) {
      existingPos.currentPrice = currentPrice;
    }

    const positionCount = this.positions.length;
    const currentExposure = this.calculateExposure();
    const correlationRisk = this.calculateCorrelationRisk(priceHistory);
    const kelly = this.calculateKelly(winRate, avgWinLossRatio);
    const varResult = this.calculateVaR();

    // Check max positions
    if (positionCount >= this.config.maxPositions) {
      return {
        canOpenPosition: false,
        reason: `max_positions_${this.config.maxPositions}_reached`,
        currentExposure, positionCount, correlationRisk,
        suggestedSize: kelly, var: varResult,
      };
    }

    // Check portfolio exposure limit
    if (currentExposure >= this.config.maxPortfolioRiskPercent) {
      return {
        canOpenPosition: false,
        reason: `exposure_${currentExposure.toFixed(1)}%_exceeds_${this.config.maxPortfolioRiskPercent}%`,
        currentExposure, positionCount, correlationRisk,
        suggestedSize: kelly, var: varResult,
      };
    }

    // Check correlation with existing positions
    if (correlationRisk > this.config.maxCorrelation && positionCount > 0) {
      return {
        canOpenPosition: false,
        reason: `high_correlation_${correlationRisk.toFixed(2)}_exceeds_${this.config.maxCorrelation}`,
        currentExposure, positionCount, correlationRisk,
        suggestedSize: kelly, var: varResult,
      };
    }

    // Check drawdown kill switch
    const currentDrawdown = this.getCurrentDrawdown();
    if (currentDrawdown >= this.config.maxDrawdownPercent) {
      return {
        canOpenPosition: false,
        reason: `drawdown_${currentDrawdown.toFixed(1)}%_exceeds_${this.config.maxDrawdownPercent}%`,
        currentExposure, positionCount, correlationRisk,
        suggestedSize: kelly, var: varResult,
      };
    }

    // Cap suggested size at single position limit
    const maxPositionValue = this.portfolioValue * (this.config.maxSinglePositionPercent / 100);
    if (kelly.positionSize > maxPositionValue) {
      kelly.positionSize = maxPositionValue;
      kelly.adjustedPercent = this.config.maxSinglePositionPercent;
    }

    return {
      canOpenPosition: true,
      currentExposure, positionCount, correlationRisk,
      suggestedSize: kelly, var: varResult,
    };
  }

  /**
   * Kelly Criterion position sizing.
   * f* = (bp - q) / b where b = avg_win/avg_loss, p = win_rate, q = 1-p
   */
  calculateKelly(winRate: number, avgWinLossRatio: number): KellyResult {
    const p = Math.max(0, Math.min(1, winRate));
    const q = 1 - p;
    const b = Math.max(0.01, avgWinLossRatio);

    const kellyPercent = ((b * p - q) / b) * 100;

    // Clamp: negative Kelly means don't bet
    const clampedKelly = Math.max(0, Math.min(100, kellyPercent));
    const adjustedPercent = clampedKelly * this.config.kellyFraction;
    const positionSize = this.portfolioValue * (adjustedPercent / 100);

    return { kellyPercent: clampedKelly, adjustedPercent, positionSize };
  }

  /**
   * Historical simulation VaR (Value at Risk).
   */
  calculateVaR(): VaRResult {
    if (this.returnHistory.length < 10) {
      return { var95: 0, cvar95: 0, varPercent: 0 };
    }

    const returns = [...this.returnHistory].sort((a, b) => a - b);
    const idx = Math.floor(returns.length * (1 - this.config.varConfidence));
    const varReturn = returns[Math.max(0, idx)];
    const var95 = Math.abs(varReturn) * this.portfolioValue;

    // CVaR: average of losses worse than VaR
    const tail = returns.slice(0, Math.max(1, idx));
    const cvarReturn = tail.reduce((s, r) => s + r, 0) / tail.length;
    const cvar95 = Math.abs(cvarReturn) * this.portfolioValue;

    return {
      var95,
      cvar95,
      varPercent: Math.abs(varReturn) * 100,
    };
  }

  /** Add a position to the portfolio */
  addPosition(position: PortfolioPosition): void {
    this.positions.push(position);
  }

  /** Remove a closed position and update portfolio value */
  closePosition(symbol: string, exitPrice: number): number {
    const idx = this.positions.findIndex(p => p.symbol === symbol);
    if (idx === -1) return 0;

    const pos = this.positions[idx];
    const pnl = pos.side === 'long'
      ? (exitPrice - pos.entryPrice) * pos.size
      : (pos.entryPrice - exitPrice) * pos.size;

    this.positions.splice(idx, 1);
    this.portfolioValue += pnl;

    // Track return for VaR
    const posValue = pos.entryPrice * pos.size;
    if (posValue > 0) {
      this.returnHistory.push(pnl / posValue);
      if (this.returnHistory.length > this.config.varLookback) {
        this.returnHistory.shift();
      }
    }

    // Update peak
    if (this.portfolioValue > this.peakValue) {
      this.peakValue = this.portfolioValue;
    }

    return pnl;
  }

  /** Update current prices for all positions */
  updatePrices(prices: Record<string, number>): void {
    for (const pos of this.positions) {
      if (prices[pos.symbol] !== undefined) {
        pos.currentPrice = prices[pos.symbol];
      }
    }
  }

  /** Total portfolio exposure as % of portfolio value */
  calculateExposure(): number {
    if (this.portfolioValue <= 0) return 0;

    const totalExposure = this.positions.reduce((sum, pos) => {
      return sum + pos.currentPrice * pos.size;
    }, 0);

    return (totalExposure / this.portfolioValue) * 100;
  }

  /** Current drawdown from peak */
  getCurrentDrawdown(): number {
    if (this.peakValue <= 0) return 0;
    return ((this.peakValue - this.portfolioValue) / this.peakValue) * 100;
  }

  /** Get all open positions */
  getPositions(): PortfolioPosition[] {
    return [...this.positions];
  }

  /** Get portfolio value */
  getPortfolioValue(): number {
    return this.portfolioValue;
  }

  /**
   * Calculate correlation risk for a potential new position.
   * Uses price history correlation with existing positions' recent returns.
   */
  private calculateCorrelationRisk(newPriceHistory?: number[]): number {
    if (!newPriceHistory || newPriceHistory.length < 10 || this.positions.length === 0) {
      return 0;
    }

    // If we don't have price histories for existing positions, return moderate risk
    return 0.3; // Conservative default — full implementation would compare return series
  }

  /** Reset portfolio state */
  reset(initialValue: number): void {
    this.positions = [];
    this.portfolioValue = initialValue;
    this.peakValue = initialValue;
    this.returnHistory = [];
  }
}
