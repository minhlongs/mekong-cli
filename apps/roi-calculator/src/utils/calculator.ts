import { CalculatorInputs, ROIResults, ChartDataPoint } from '../types';

const DISCOUNT_RATE = 0.10; // 10% annual discount rate for NPV

/**
 * Calculate monthly costs for current setup
 */
export function calculateCurrentMonthlyCost(inputs: CalculatorInputs): number {
  const monthlySalary = (inputs.currentAvgSalary * inputs.currentEngineerCount) / 12;
  return monthlySalary + inputs.currentToolCosts + inputs.currentOpexMonthly;
}

/**
 * Calculate monthly costs for Mekong CLI
 */
export function calculateMekongMonthlyCost(inputs: CalculatorInputs): number {
  const mcuCost = inputs.mekongMcuUsage * inputs.mekongMcuPrice;
  return inputs.mekongSubscription + mcuCost;
}

/**
 * Calculate payback period in months
 */
function calculatePaybackMonths(
  currentMonthly: number,
  mekongMonthly: number,
  initialInvestment: number = 0
): number {
  const monthlySavings = currentMonthly - mekongMonthly;
  if (monthlySavings <= 0) return Infinity;
  return Math.ceil(initialInvestment / monthlySavings);
}

/**
 * Calculate Net Present Value
 */
function calculateNPV(
  monthlySavings: number,
  months: number,
  discountRate: number = DISCOUNT_RATE
): number {
  const monthlyRate = discountRate / 12;
  let npv = 0;
  for (let i = 1; i <= months; i++) {
    npv += monthlySavings / Math.pow(1 + monthlyRate, i);
  }
  return npv;
}

/**
 * Calculate ROI percentage
 */
function calculateROIPercent(
  totalSavings: number,
  totalInvestment: number
): number {
  if (totalInvestment === 0) return 0;
  return ((totalSavings - totalInvestment) / totalInvestment) * 100;
}

/**
 * Main calculator function
 */
export function calculateROI(inputs: CalculatorInputs): ROIResults {
  const currentMonthlyCost = calculateCurrentMonthlyCost(inputs);
  const mekongMonthlyCost = calculateMekongMonthlyCost(inputs);
  const monthlySavings = currentMonthlyCost - mekongMonthlyCost;

  const totalMonths = inputs.projectionYears * 12;

  const currentTotalCost = currentMonthlyCost * totalMonths;
  const mekongTotalCost = mekongMonthlyCost * totalMonths;
  const totalSavings = currentTotalCost - mekongTotalCost;

  const savingsPercent = currentTotalCost > 0
    ? (totalSavings / currentTotalCost) * 100
    : 0;

  const paybackMonths = monthlySavings > 0
    ? calculatePaybackMonths(currentMonthlyCost, mekongMonthlyCost, 0)
    : Infinity;

  const npv = calculateNPV(monthlySavings, totalMonths);

  // 3-year ROI (standardized)
  const threeYearMonths = 36;
  const threeYearSavings = monthlySavings * threeYearMonths;
  const threeYearMekongCost = mekongMonthlyCost * threeYearMonths;
  const threeYearRoi = calculateROIPercent(threeYearSavings, threeYearMekongCost);

  return {
    currentTotalCost,
    mekongTotalCost,
    totalSavings,
    savingsPercent,
    paybackMonths,
    threeYearRoi,
    npv,
    currentMonthlyCost,
    mekongMonthlyCost,
    monthlySavings
  };
}

/**
 * Generate chart data for visualization
 */
export function generateChartData(inputs: CalculatorInputs): ChartDataPoint[] {
  const data: ChartDataPoint[] = [];
  const currentMonthly = calculateCurrentMonthlyCost(inputs);
  const mekongMonthly = calculateMekongMonthlyCost(inputs);

  let cumulativeCurrent = 0;
  let cumulativeMekong = 0;

  const totalMonths = Math.min(inputs.projectionYears * 12, 60); // Max 5 years

  for (let month = 1; month <= totalMonths; month++) {
    cumulativeCurrent += currentMonthly;
    cumulativeMekong += mekongMonthly;

    data.push({
      month,
      currentCost: Math.round(cumulativeCurrent),
      mekongCost: Math.round(cumulativeMekong),
      cumulativeSavings: Math.round(cumulativeCurrent - cumulativeMekong)
    });
  }

  return data;
}

/**
 * Format currency for display
 */
export function formatCurrency(value: number, locale: string = 'en-US'): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
}

/**
 * Format percentage for display
 */
export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

/**
 * Format months to years/months
 */
export function formatDuration(months: number): string {
  if (months === Infinity) return 'N/A';
  if (months >= 12) {
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    return remainingMonths > 0 ? `${years}y ${remainingMonths}m` : `${years}y`;
  }
  return `${months}m`;
}
