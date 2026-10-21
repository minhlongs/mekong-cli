/**
 * ROI Dashboard — Calculate time saved, cost efficiency, and ROI multiplier
 *
 * Reads metering data and calculates:
 * - Time saved per command vs manual coding
 * - Cost per agent call
 * - Total ROI multiplier
 */
import type { UsageEvent } from '../metering/types.js';
import { UsageAnalyzer } from '../metering/analyzer.js';
import {
  DEVELOPER_HOURLY_RATE,
  calculateCategoryTimeSaved,
  calculateEfficiencyGainPercent,
  createEmptyRoiMetrics,
} from './roi-dashboard-helpers.js';

/** ROI metrics snapshot */
export interface RoiMetrics {
  total_time_saved_seconds: number;
  total_time_saved_hours: number;
  time_saved_by_category: {
    commands: number;
    tests: number;
    docs: number;
    debug: number;
  };
  cost: {
    total_llm_cost_usd: number;
    cost_per_agent_call: number;
    cost_per_command: number;
  };
  value: {
    labor_cost_saved_usd: number;
    net_value_usd: number;
    roi_multiplier: number;
  };
  productivity: {
    total_commands: number;
    avg_time_saved_per_command: number;
    efficiency_gain_percent: number;
  };
  period: {
    start_date: string;
    end_date: string;
    days_tracked: number;
  };
}

/** Detailed breakdown by day */
export interface DailyRoiBreakdown {
  date: string;
  time_saved_seconds: number;
  llm_cost_usd: number;
  net_value_usd: number;
  roi_multiplier: number;
}

/**
 * ROI Dashboard Service
 */
export class RoiDashboard {
  private analyzer: UsageAnalyzer;

  constructor() {
    this.analyzer = new UsageAnalyzer();
  }

  /**
   * Calculate ROI metrics from usage events
   */
  calculateRoi(events: UsageEvent[]): RoiMetrics {
    if (events.length === 0) {
      return createEmptyRoiMetrics();
    }

    const summary = this.analyzer.summarize(events);
    const readings = summary.readings;

    const timeSaved = calculateCategoryTimeSaved(events);
    const totalTimeSavedSeconds =
      timeSaved.commands + timeSaved.tests + timeSaved.docs + timeSaved.debug;

    const totalLlmCost = summary.totals.totalCostUsd;
    const totalCommands = events.filter(
      e => e.category === 'tool_run' || e.category === 'sop_run',
    ).length;
    const agentCalls = events.filter(e => e.category === 'llm_call').length;

    const costPerAgentCall = agentCalls > 0 ? totalLlmCost / agentCalls : 0;
    const costPerCommand = totalCommands > 0 ? totalLlmCost / totalCommands : 0;

    const totalTimeSavedHours = totalTimeSavedSeconds / 3600;
    const laborCostSaved = totalTimeSavedHours * DEVELOPER_HOURLY_RATE;
    const netValue = laborCostSaved - totalLlmCost;
    const roiMultiplier = totalLlmCost > 0 ? laborCostSaved / totalLlmCost : 0;

    const dates = events.map(e => e.timestamp).sort();
    const startDate = dates[0]?.slice(0, 10) || '';
    const endDate = dates[dates.length - 1]?.slice(0, 10) || '';

    return {
      total_time_saved_seconds: totalTimeSavedSeconds,
      total_time_saved_hours: totalTimeSavedHours,
      time_saved_by_category: timeSaved,
      cost: {
        total_llm_cost_usd: totalLlmCost,
        cost_per_agent_call: costPerAgentCall,
        cost_per_command: costPerCommand,
      },
      value: {
        labor_cost_saved_usd: laborCostSaved,
        net_value_usd: netValue,
        roi_multiplier: roiMultiplier,
      },
      productivity: {
        total_commands: totalCommands,
        avg_time_saved_per_command: totalCommands > 0 ? totalTimeSavedSeconds / totalCommands : 0,
        efficiency_gain_percent: calculateEfficiencyGainPercent(events),
      },
      period: {
        start_date: startDate,
        end_date: endDate,
        days_tracked: readings.length,
      },
    };
  }

  /**
   * Get daily ROI breakdown
   */
  getDailyBreakdown(events: UsageEvent[]): DailyRoiBreakdown[] {
    const summary = this.analyzer.summarize(events);

    return summary.readings.map(reading => {
      const dayEvents = events.filter(e => e.timestamp.startsWith(reading.date));
      const timeSaved = calculateCategoryTimeSaved(dayEvents);
      const totalTimeSavedSeconds =
        timeSaved.commands + timeSaved.tests + timeSaved.docs + timeSaved.debug;
      const totalTimeSavedHours = totalTimeSavedSeconds / 3600;
      const laborCostSaved = totalTimeSavedHours * DEVELOPER_HOURLY_RATE;
      const llmCost = reading.totalCostUsd;
      const netValue = laborCostSaved - llmCost;
      const roiMultiplier = llmCost > 0 ? laborCostSaved / llmCost : 0;

      return {
        date: reading.date,
        time_saved_seconds: totalTimeSavedSeconds,
        llm_cost_usd: llmCost,
        net_value_usd: netValue,
        roi_multiplier: roiMultiplier,
      };
    });
  }

  /**
   * Export ROI data as JSON for frontend
   */
  exportJson(events: UsageEvent[]): object {
    const metrics = this.calculateRoi(events);
    const daily = this.getDailyBreakdown(events);

    return {
      generated_at: new Date().toISOString(),
      metrics,
      daily_breakdown: daily,
      summary: {
        total_roi_multiplier: metrics.value.roi_multiplier.toFixed(2),
        total_net_value_usd: metrics.value.net_value_usd.toFixed(2),
        total_time_saved_hours: metrics.total_time_saved_hours.toFixed(2),
        total_llm_cost_usd: metrics.cost.total_llm_cost_usd.toFixed(6),
      },
    };
  }
}

/** Export singleton instance */
export const roiDashboard = new RoiDashboard();
