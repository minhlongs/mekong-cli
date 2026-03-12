/**
 * AI-Powered Improvement Recommender.
 * Generates actionable suggestions from KaizenAnalyzer results.
 */
import { randomUUID } from 'crypto';
import type { KaizenSuggestion, Bottleneck, SopAnalytics, AgentAnalytics } from './types.js';
import type { LlmRouter } from '../llm/router.js';
import { ok, err } from '../types/common.js';
import type { Result } from '../types/common.js';

export class KaizenRecommender {
  constructor(private readonly llm: LlmRouter) {}

  /** Generate suggestions from analysis results */
  async suggest(input: {
    sopAnalytics: SopAnalytics[];
    agentAnalytics: AgentAnalytics[];
    bottlenecks: Bottleneck[];
    budgetData: { totalSpent: number; byModel: Record<string, number> };
  }): Promise<KaizenSuggestion[]> {
    const suggestions: KaizenSuggestion[] = [];
    const now = new Date().toISOString();

    // Rule 1: step consumes >50% of SOP time → parallelize or optimize
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
      }
    }

    // Rule 2: step success 100% + retryRate 0 → candidate to skip
    for (const sop of input.sopAnalytics) {
      for (const step of sop.stepAnalytics) {
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

    // Rule 3: expensive model for simple tasks → downgrade
    const modelEntries = Object.entries(input.budgetData.byModel);
    for (const [model, spent] of modelEntries) {
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

    // Rule 4: low agent efficiency score → prompt_optimize
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

    // Rule 5: critical bottlenecks → tool_change
    for (const bn of input.bottlenecks) {
      if (bn.impact === 'critical' && bn.type === 'tool') {
        suggestions.push({
          id: randomUUID(),
          type: 'tool_change',
          title: `Replace unreliable tool "${bn.location}"`,
          description: `Tool failure rate at ${bn.currentValue.toFixed(0)}% (expected <${bn.expectedValue}%).`,
          target: bn.location,
          evidence: `${bn.currentValue.toFixed(0)}% failure rate`,
          estimatedImpact: {
            timeSaved: 0,
            costSaved: 0,
            successRateChange: 10,
          },
          autoApplicable: false,
          status: 'proposed',
          createdAt: now,
        });
      }
    }

    // AI-powered: call LLM only if we have enough data and bottlenecks
    if (input.bottlenecks.length > 0 && input.sopAnalytics.length > 0) {
      try {
        const aiSuggestions = await this.generateAiSuggestions(input, now);
        suggestions.push(...aiSuggestions);
      } catch {
        // LLM unavailable — rule-based suggestions still returned
      }
    }

    return suggestions;
  }

  /** Apply a suggestion automatically (for auto-applicable ones) */
  async apply(suggestion: KaizenSuggestion): Promise<Result<void>> {
    if (!suggestion.autoApplicable) {
      return err(new Error(`Suggestion "${suggestion.id}" requires manual approval`));
    }
    if (suggestion.type === 'model_downgrade') {
      // In production: update agent routing config — stubbed here as config write
      suggestion.status = 'applied';
      suggestion.appliedAt = new Date().toISOString();
      return ok(undefined);
    }
    if (suggestion.type === 'cache') {
      suggestion.status = 'applied';
      suggestion.appliedAt = new Date().toISOString();
      return ok(undefined);
    }
    return err(new Error(`Auto-apply not supported for type "${suggestion.type}"`));
  }

  /** Revert an applied suggestion */
  async revert(suggestionId: string): Promise<Result<void>> {
    // In production: undo config changes written by apply()
    // Stubbed: just return ok — actual config reversal requires persistence layer
    void suggestionId;
    return ok(undefined);
  }

  private async generateAiSuggestions(
    input: {
      sopAnalytics: SopAnalytics[];
      bottlenecks: Bottleneck[];
    },
    now: string,
  ): Promise<KaizenSuggestion[]> {
    const summary = JSON.stringify({
      sops: input.sopAnalytics.map(s => ({
        name: s.sopName,
        successRate: s.successRate,
        avgDuration: s.avgDuration,
        trend: s.trend,
      })),
      topBottlenecks: input.bottlenecks.slice(0, 3),
    });

    const response = await this.llm.chat({
      messages: [
        {
          role: 'system',
          content: 'You are a performance optimization expert. Return JSON array of suggestions.',
        },
        {
          role: 'user',
          content: `Analyze this system performance data and suggest ONE structural improvement:\n${summary}\n\nReturn JSON: [{"type":"sop_restructure","title":"...","description":"...","target":"...","evidence":"..."}]`,
        },
      ],
      maxTokens: 400,
    });

    try {
      const text = response.content.trim();
      const jsonMatch = text.match(/\[[\s\S]*\]/);
      if (!jsonMatch) return [];
      const raw = JSON.parse(jsonMatch[0]) as Array<{
        type: KaizenSuggestion['type'];
        title: string;
        description: string;
        target: string;
        evidence: string;
      }>;
      return raw.slice(0, 2).map(r => ({
        id: randomUUID(),
        type: r.type ?? 'sop_restructure',
        title: r.title ?? 'AI-suggested improvement',
        description: r.description ?? '',
        target: r.target ?? 'system',
        evidence: r.evidence ?? 'AI analysis',
        estimatedImpact: { timeSaved: 0, costSaved: 0, successRateChange: 0 },
        autoApplicable: false,
        status: 'proposed' as const,
        createdAt: now,
      }));
    } catch {
      return [];
    }
  }
}
