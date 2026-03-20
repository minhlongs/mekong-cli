/**
 * ROI Calculator Types
 * Mekong CLI - AI-operated business platform
 */

export interface CalculatorInputs {
  // Current costs (monthly)
  currentEngineerCount: number;
  currentAvgSalary: number; // Annual salary per engineer
  currentToolCosts: number; // Monthly tooling costs
  currentOpexMonthly: number; // Other operational expenses

  // Mekong CLI costs
  mekongSubscription: number; // Monthly subscription ($49/$149/$499)
  mekongMcuUsage: number; // Monthly MCU consumption
  mekongMcuPrice: number; // Price per MCU (default $0.29)

  // Time horizon
  projectionYears: number; // 1, 3, 5
}

export interface ROIResults {
  // Cost breakdowns
  currentTotalCost: number; // Total current cost over projection
  mekongTotalCost: number; // Total Mekong cost over projection

  // Savings
  totalSavings: number; // Absolute savings
  savingsPercent: number; // Percentage savings

  // ROI metrics
  paybackMonths: number; // Months to break even
  threeYearRoi: number; // 3-year ROI percentage
  npv: number; // Net Present Value (10% discount rate)

  // Monthly breakdown
  currentMonthlyCost: number;
  mekongMonthlyCost: number;
  monthlySavings: number;
}

export interface ChartDataPoint {
  month: number;
  currentCost: number;
  mekongCost: number;
  cumulativeSavings: number;
}

export interface PresetScenario {
  name: string;
  description: string;
  inputs: Partial<CalculatorInputs>;
}
