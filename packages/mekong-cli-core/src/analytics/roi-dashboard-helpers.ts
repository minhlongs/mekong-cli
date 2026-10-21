/**
 * ROI Dashboard Helpers — Time saved & productivity calculations for RoiDashboard.
 */
import type { UsageEvent } from '../metering/types.js';
import type { RoiMetrics } from './roi-dashboard.js';

/** Average developer hourly rate (USD) */
export const DEVELOPER_HOURLY_RATE = 50;

/** Average manual time per command type (seconds) */
export const MANUAL_TIME_BENCHMARKS: Record<string, number> = {
  code_generation: 900, // 15 min manual vs 30s AI
  test_writing: 1200, // 20 min manual vs 45s AI
  documentation: 600, // 10 min manual vs 20s AI
  debugging: 1800, // 30 min manual vs 60s AI
  refactoring: 1500, // 25 min manual vs 40s AI
  code_review: 900, // 15 min manual vs 25s AI
  default: 600, // 10 min default
};

export interface CategoryTimeSaved {
  commands: number;
  tests: number;
  docs: number;
  debug: number;
}

export function calculateCategoryTimeSaved(events: UsageEvent[]): CategoryTimeSaved {
  const result: CategoryTimeSaved = { commands: 0, tests: 0, docs: 0, debug: 0 };

  for (const event of events) {
    if (event.category === 'tool_run') {
      const toolName = event.toolName?.toLowerCase() || '';
      const aiTimeSeconds = event.durationMs / 1000;

      if (toolName.includes('test')) {
        const manualTime = MANUAL_TIME_BENCHMARKS.test_writing;
        result.tests += Math.max(0, manualTime - aiTimeSeconds);
      } else if (toolName.includes('doc')) {
        const manualTime = MANUAL_TIME_BENCHMARKS.documentation;
        result.docs += Math.max(0, manualTime - aiTimeSeconds);
      } else if (toolName.includes('debug')) {
        const manualTime = MANUAL_TIME_BENCHMARKS.debugging;
        result.debug += Math.max(0, manualTime - aiTimeSeconds);
      } else {
        const manualTime = MANUAL_TIME_BENCHMARKS.default;
        result.commands += Math.max(0, manualTime - aiTimeSeconds);
      }
    } else if (event.category === 'sop_run') {
      const aiTimeSeconds = event.durationMs / 1000;
      const manualTime = MANUAL_TIME_BENCHMARKS.code_generation * event.stepCount;
      result.commands += Math.max(0, manualTime - aiTimeSeconds);
    }
  }

  return result;
}

export function calculateEfficiencyGainPercent(events: UsageEvent[]): number {
  let totalManualTime = 0;
  let totalAiTime = 0;

  for (const event of events) {
    if (event.category === 'tool_run' || event.category === 'sop_run') {
      const aiTimeSeconds = event.durationMs / 1000;
      const manualTime =
        event.category === 'sop_run'
          ? MANUAL_TIME_BENCHMARKS.code_generation * event.stepCount
          : MANUAL_TIME_BENCHMARKS.default;

      totalManualTime += manualTime;
      totalAiTime += aiTimeSeconds;
    }
  }

  if (totalManualTime === 0) return 0;
  return ((totalManualTime - totalAiTime) / totalManualTime) * 100;
}

export function createEmptyRoiMetrics(): RoiMetrics {
  return {
    total_time_saved_seconds: 0,
    total_time_saved_hours: 0,
    time_saved_by_category: { commands: 0, tests: 0, docs: 0, debug: 0 },
    cost: {
      total_llm_cost_usd: 0,
      cost_per_agent_call: 0,
      cost_per_command: 0,
    },
    value: {
      labor_cost_saved_usd: 0,
      net_value_usd: 0,
      roi_multiplier: 0,
    },
    productivity: {
      total_commands: 0,
      avg_time_saved_per_command: 0,
      efficiency_gain_percent: 0,
    },
    period: {
      start_date: '',
      end_date: '',
      days_tracked: 0,
    },
  };
}
