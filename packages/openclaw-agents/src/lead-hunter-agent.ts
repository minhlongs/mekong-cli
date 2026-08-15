/**
 * Lead Hunter Agent — prospects discovery and scoring
 * Routes to DeepSeek-R1-Distill-32B (worker) for precise, structured analysis
 */

import type { AgentDefinition } from './types.js';

export const leadHunterAgent: AgentDefinition = {
  id: 'lead-hunter',
  name: 'Lead Hunter',
  description: 'Identifies and scores B2B prospects matching ideal customer profile (ICP)',
  capability: 'lead-generation',
  modelPreference: 'worker',
  systemPrompt:
    'Analyze industry data to identify prospects that match the provided ICP criteria. ' +
    'Score each lead from 1-100 based on fit, intent signals, and company health indicators. ' +
    'Extract verified contact information and enrich with firmographic data. ' +
    'Prioritize quality over quantity — return only leads scoring above 60.',
  tools: [
    {
      name: 'web_search',
      description: 'Search the web for company and contact information',
      parameters: { query: { type: 'string' }, maxResults: { type: 'number' } },
    },
    {
      name: 'company_lookup',
      description: 'Retrieve firmographic data for a given company domain',
      parameters: { domain: { type: 'string' } },
    },
    {
      name: 'lead_score',
      description: 'Score a lead 1-100 based on ICP fit criteria',
      parameters: { leadData: { type: 'object' }, icpCriteria: { type: 'object' } },
    },
  ],
  maxTokens: 4096,
  temperature: 0.3,
};
