/**
 * Rule-based Kaizen suggestion rules.
 */
import { randomUUID } from 'crypto';
import type { KaizenSuggestion, Bottleneck, SopAnalytics, AgentAnalytics } from './types.js';

export function buildRuleSuggestions(
  input: {
    sopAnalytics: SopAnalytics[];
    agentAnalytics: AgentAnalytics[];
    bottlenecks: Bottleneck[];
    budgetData: { totalSpent: number; byModel: Record<string, number> };
  },
  now: string,
): KaizenSuggestion[] {
  const suggestions: KaizenSuggestion[] = [];

  for (const sop of input.sopAnalytics) {
    for (const step of sop.stepAnalytics) {
      if (step.percentOfTotal > 50) {
        suggestions.push({
          id: randomUUID(),
          type: 'parallelize',
          title: `Parallelize bottleneck step "${step.stepId}" in ${sop.sopName}`,
          description: `Step "${step.stepId}" consumes ${step.percentOfTotal.toFixed(0)}% of total SOP time.`,
          target: `${sop.sopName}.${step.stepId}`,
          evidence: `${step.percentOfTotal.toFixed(1)}% of total duration, avg ${step.avgDuration.toFixed(1)}s`,
          estimatedImpact: {
            timeSaved: sop.avgDuration * (step.percentOfTotal / 100) * 0.4,
            costSaved: 0,
            successRateChange: 0,
          },
          autoApplicable: false,
          status: 'proposed',
          createdAt: now,
        });
      }
      if (step.successRate === 100 && step.retryRate === 0 && step.percentOfTotal < 5) {
        suggestions.push({
          id: randomUUID(),
          type: 'skip_step',
          title: `Consider skipping low-value step "${step.stepId}"`,
          description: `Step always succeeds with no retries and contributes only ${step.percentOfTotal.toFixed(1)}% of duration.`,
          target: `${sop.sopName}.${step.stepId}`,
          evidence: `100% success, 0% retry, ${step.percentOfTotal.toFixed(1)}% time share`,
          estimatedImpact: {
            timeSaved: step.avgDuration,
            costSaved: sop.avgCost * (step.costContribution / 100),
            successRateChange: 0,
          },
          autoApplicable: false,
          status: 'proposed',
          createdAt: now,
        });
      }
    }
  }

  for (const [model, spent] of Object.entries(input.budgetData.byModel)) {
    if (spent > input.budgetData.totalSpent * 0.4 && (model.includes('opus') || model.includes('gpt-4'))) {
      suggestions.push({
        id: randomUUID(),
        type: 'model_downgrade',
        title: `Switch from ${model} to cheaper model for routine tasks`,
        description: `${model} accounts for ${((spent / (input.budgetData.totalSpent || 1)) * 100).toFixed(0)}% of total LLM spend.`,
        target: model,
        evidence: `$${spent.toFixed(2)} of $${input.budgetData.totalSpent.toFixed(2)} total`,
        estimatedImpact: {
          timeSaved: 0,
          costSaved: spent * 0.5,
          successRateChange: -1,
        },
        autoApplicable: true,
        status: 'proposed',
        createdAt: now,
      });
    }
  }

  for (const agent of input.agentAnalytics) {
    if (agent.efficiencyScore < 50 && agent.avgTokensPerTask > 3000) {
      suggestions.push({
        id: randomUUID(),
        type: 'prompt_optimize',
        title: `Optimize prompts for agent "${agent.agentName}"`,
        description: `Agent uses ${agent.avgTokensPerTask.toFixed(0)} tokens/task on average with ${agent.successRate.toFixed(0)}% success.`,
        target: agent.agentName,
        evidence: `Efficiency score: ${agent.efficiencyScore.toFixed(0)}/100, avg tokens: ${agent.avgTokensPerTask.toFixed(0)}`,
        estimatedImpact: {
          timeSaved: 0,
          costSaved: agent.avgCostPerTask * agent.totalTasks * 0.2,
          successRateChange: 5,
        },
        autoApplicable: false,
        status: 'proposed',
        createdAt: now,
      });
    }
  }

  for (const bn of input.bottlenecks) {
    if (bn.impact === 'critical' && bn.type === 'tool') {
      suggestions.push({
        id: randomUUID(),
        type: 'tool_change',
        title: `Replace unreliable tool "${bn.location}"`,
        description: `Tool failure rate at ${bn.currentValue.toFixed(0)}% (expected <${bn.expectedValue}%).`,
        target: bn.location,
        evidence: `${bn.currentValue.toFixed(0)}% failure rate`,
        estimatedImpact: { timeSaved: 0, costSaved: 0, successRateChange: 10 },
        autoApplicable: false,
        status: 'proposed',
        createdAt: now,
      });
    }
  }

  return suggestions;
}
