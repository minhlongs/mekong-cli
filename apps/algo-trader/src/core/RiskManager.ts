export class RiskManager {
  /**
   * Calculate position size based on account balance and risk percentage
   * @param balance Current account balance
   * @param riskPercentage Risk per trade (e.g., 1 for 1%)
   * @param currentPrice Current price of the asset
   * @returns Amount to buy
   */
  static calculatePositionSize(balance: number, riskPercentage: number, currentPrice: number): number {
    if (riskPercentage <= 0 || riskPercentage > 100) {
      throw new Error("Risk percentage must be between 0 and 100");
    }

    const amountToRisk = balance * (riskPercentage / 100);
    // Simplified: assuming we buy with the full risked amount effectively used as margin or cost
    // In a real scenario with Stop Loss, this calculation is: (RiskAmount) / (Entry - StopLoss)
    // Here we implement the prompt's "Position Sizing 1%" which likely means "Use 1% of balance to buy"

    return amountToRisk / currentPrice;
  }
}
