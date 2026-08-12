/**
 * Sales Ops Agent — deal management and proposal automation
 * Routes to DeepSeek-R1-Distill-32B (worker) for structured sales document generation
 */

import type { AgentDefinition } from './types.js';

export const salesOpsAgent: AgentDefinition = {
  id: 'sales-ops',
  name: 'Sales Ops',
  description: 'Automates discovery prep, proposal writing, follow-ups, and deal stage tracking',
  capability: 'sales-operations',
  modelPreference: 'worker',
  systemPrompt:
    'Prepare discovery call documents by researching prospect company, stakeholders, and pain points. ' +
    'Write proposal summaries that map product capabilities directly to stated buyer objectives. ' +
    'Generate personalized follow-up emails within 24 hours of each touchpoint, referencing specific conversation details. ' +
    'Track deal stage transitions and flag stalled opportunities that have not progressed in 7 days.',
  tools: [
    {
      name: 'deal_summary',
      description: 'Generate a structured summary of deal status, stakeholders, and next steps',
      parameters: { dealId: { type: 'string' }, crmData: { type: 'object' } },
    },
    {
      name: 'proposal_draft',
      description: 'Draft a solution proposal aligned to prospect objectives',
      parameters: { prospectName: { type: 'string' }, objectives: { type: 'array' }, tier: { type: 'string' } },
    },
    {
      name: 'followup_email',
      description: 'Write a personalized follow-up email after a sales interaction',
      parameters: { recipientName: { type: 'string' }, meetingNotes: { type: 'string' }, nextStep: { type: 'string' } },
    },
  ],
  maxTokens: 4096,
  temperature: 0.4,
};
