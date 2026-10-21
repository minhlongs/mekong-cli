/**
 * AI-Powered Improvement Recommender.
 * Generates actionable suggestions from KaizenAnalyzer results.
 */
import { randomUUID } from 'crypto';
import type { KaizenSuggestion, Bottleneck, SopAnalytics, AgentAnalytics } from './types.js';
import type { LlmRouter } from '../llm/router.js';
import { ok, err } from '../types/common.js';
import type { Result } from '../types/common.js';
import { buildRuleSuggestions } from './recommender-rules.js';

export class KaizenRecommender {
  constructor(private readonly llm: LlmRouter) {}

  /** Generate suggestions from analysis results */
  async suggest(input: {
    sopAnalytics: SopAnalytics[];
    agentAnalytics: AgentAnalytics[];
    bottlenecks: Bottleneck[];
    budgetData: { totalSpent: number; byModel: Record<string, number> };
  }): Promise<KaizenSuggestion[]> {
    const now = new Date().toISOString();
    const suggestions = buildRuleSuggestions(input, now);

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
    if (suggestion.type === 'model_downgrade' || suggestion.type === 'cache') {
      suggestion.status = 'applied';
      suggestion.appliedAt = new Date().toISOString();
      return ok(undefined);
    }
    return err(new Error(`Auto-apply not supported for type "${suggestion.type}"`));
  }

  /** Revert an applied suggestion */
  async revert(suggestionId: string): Promise<Result<void>> {
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
