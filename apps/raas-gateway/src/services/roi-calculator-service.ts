/**
 * ROI Calculator — estimate savings from using RaaS platform
 */

export interface RoiInput {
  team_size: number;
  missions_per_month: number;
  current_monthly_cost: number;
  avg_mission_time_hours?: number;
}

export interface RoiResult {
  input: RoiInput;
  recommended_tier: string;
  monthly_cost: number;
  annual_cost: number;
  monthly_savings: number;
  annual_savings: number;
  roi_percentage: number;
  payback_days: number;
  time_saved_hours: number;
  efficiency_gain: string;
}

const TIERS = [
  { name: 'starter', price: 29, mcu: 50 },
  { name: 'pro', price: 99, mcu: 200 },
  { name: 'agency', price: 199, mcu: 500 },
  { name: 'master', price: 399, mcu: 1000 },
  { name: 'enterprise', price: 999, mcu: -1 },
];

export class RoiCalculatorService {
  calculate(input: RoiInput): RoiResult {
    const missionsNeeded = input.missions_per_month;
    // Find cheapest tier that covers missions
    const tier = TIERS.find(t => t.mcu === -1 || t.mcu >= missionsNeeded) || TIERS[TIERS.length - 1];

    const monthlyCost = tier.price;
    const annualCost = monthlyCost * 12;
    const monthlySavings = input.current_monthly_cost - monthlyCost;
    const annualSavings = monthlySavings * 12;
    const roiPct = input.current_monthly_cost > 0
      ? Math.round((annualSavings / annualCost) * 100)
      : 0;
    const avgTime = input.avg_mission_time_hours || 2;
    const timeSaved = missionsNeeded * avgTime * 0.8; // 80% time reduction
    const paybackDays = monthlySavings > 0 ? Math.ceil(monthlyCost / (monthlySavings / 30)) : 0;

    return {
      input,
      recommended_tier: tier.name,
      monthly_cost: monthlyCost,
      annual_cost: annualCost,
      monthly_savings: Math.max(0, monthlySavings),
      annual_savings: Math.max(0, annualSavings),
      roi_percentage: Math.max(0, roiPct),
      payback_days: Math.max(0, paybackDays),
      time_saved_hours: Math.round(timeSaved),
      efficiency_gain: `${Math.round(timeSaved / (missionsNeeded * avgTime) * 100)}%`,
    };
  }
}
