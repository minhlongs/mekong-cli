/**
 * Agent Scorer — AGI Score (0-100) per HIEN-PHAP Điều 7.3.
 * Weights: phaseProgress 30%, activity 25%, successRate 25%, resilience 20%.
 */
import type { AgentPerformance } from './types.js';

export interface AgentScoreInputs {
  agentName: string;
  /** Completed phases out of total */
  phasesCompleted: number;
  totalPhases: number;
  /** Recent commits or task completions (activity proxy) */
  recentCommits: number;
  /** Baseline for "full" activity (e.g. 10 commits = 100%) */
  activityBaseline: number;
  /** Total executions attempted */
  totalExecutions: number;
  /** Successful executions */
  successfulExecutions: number;
  /** Executions recovered after error (subset of failed) */
  recoveredExecutions: number;
  /** Failed executions (non-recovered) */
  failedExecutions: number;
}

const WEIGHTS = {
  phaseProgress: 0.30,
  activity: 0.25,
  successRate: 0.25,
  resilience: 0.20,
} as const;

export class AgentScorer {
  /**
   * Compute AGI score for a single agent.
   * Each component is normalized 0-100 before weighting.
   */
  score(inputs: AgentScoreInputs): AgentPerformance {
    const {
      agentName,
      phasesCompleted,
      totalPhases,
      recentCommits,
      activityBaseline,
      totalExecutions,
      successfulExecutions,
      recoveredExecutions,
      failedExecutions,
    } = inputs;

    // Phase progress score (0-100)
    const phaseProgressScore = totalPhases > 0
      ? Math.min(100, (phasesCompleted / totalPhases) * 100)
      : 0;

    // Activity score (0-100): commits relative to baseline
    const activityScore = activityBaseline > 0
      ? Math.min(100, (recentCommits / activityBaseline) * 100)
      : recentCommits > 0 ? 100 : 0;

    // Success rate score (0-100)
    const successRate = totalExecutions > 0
      ? successfulExecutions / totalExecutions
      : 1; // No runs = assume perfect (no failures)
    const successRateScore = successRate * 100;

    // Resilience: error recovery rate (recovered / (failed + recovered))
    const totalProblematic = failedExecutions + recoveredExecutions;
    const errorRecoveryRate = totalProblematic > 0
      ? recoveredExecutions / totalProblematic
      : 1;
    const resilienceScore = errorRecoveryRate * 100;

    // Weighted AGI score
    const agiScore = Math.round(
      phaseProgressScore * WEIGHTS.phaseProgress +
      activityScore * WEIGHTS.activity +
      successRateScore * WEIGHTS.successRate +
      resilienceScore * WEIGHTS.resilience,
    );

    return {
      agentName,
      agiScore: Math.min(100, Math.max(0, agiScore)),
      phaseProgressScore: Math.round(phaseProgressScore),
      activityScore: Math.round(activityScore),
      successRateScore: Math.round(successRateScore),
      resilienceScore: Math.round(resilienceScore),
      totalExecutions,
      successfulExecutions,
      failedExecutions,
      successRate: Math.round(successRate * 1000) / 1000,
      errorRecoveryRate: Math.round(errorRecoveryRate * 1000) / 1000,
      recentCommits,
      phasesCompleted,
      totalPhases,
      computedAt: new Date().toISOString(),
    };
  }

  /** Score multiple agents, sort by agiScore descending */
  scoreAll(inputs: AgentScoreInputs[]): AgentPerformance[] {
    return inputs
      .map((i) => this.score(i))
      .sort((a, b) => b.agiScore - a.agiScore);
  }

  /** Format leaderboard for CLI */
  formatLeaderboard(agents: AgentPerformance[]): string {
    if (agents.length === 0) return '\nNo agent data available.\n';
    const lines: string[] = ['\nAGI Score Leaderboard\n', pad('Agent', 'Score', 'Success%', 'Resilience')];
    lines.push('─'.repeat(52));
    for (const a of agents) {
      lines.push(pad(
        a.agentName,
        String(a.agiScore),
        `${(a.successRate * 100).toFixed(0)}%`,
        `${(a.errorRecoveryRate * 100).toFixed(0)}%`,
      ));
    }
    lines.push('');
    return lines.join('\n');
  }
}

function pad(c1: string, c2: string, c3: string, c4: string): string {
  return `  ${c1.padEnd(22)}${c2.padStart(6)}  ${c3.padStart(8)}  ${c4.padStart(10)}`;
}
