/**
 * Support Bot Agent — ticket classification and response drafting
 * Routes to DeepSeek-R1-Distill-32B (worker) for consistent, deterministic triage
 */

import type { AgentDefinition } from './types.js';

export const supportBotAgent: AgentDefinition = {
  id: 'support-bot',
  name: 'Support Bot',
  description: 'Classifies support tickets and drafts accurate responses from knowledge base',
  capability: 'customer-support',
  modelPreference: 'worker',
  systemPrompt:
    'Classify incoming support tickets into one of: bug, feature-request, billing, or how-to. ' +
    'Search the knowledge base for relevant solutions before drafting any response. ' +
    'Draft concise, empathetic replies that resolve the issue in one interaction where possible. ' +
    'For billing disputes, escalate to human agents — never make refund commitments autonomously.',
  tools: [
    {
      name: 'ticket_classify',
      description: 'Classify a support ticket into bug, feature-request, billing, or how-to',
      parameters: { subject: { type: 'string' }, body: { type: 'string' } },
    },
    {
      name: 'kb_search',
      description: 'Search the knowledge base for articles matching the issue',
      parameters: { query: { type: 'string' }, maxResults: { type: 'number' } },
    },
    {
      name: 'response_draft',
      description: 'Draft a customer-facing response from a KB article and ticket context',
      parameters: { ticketId: { type: 'string' }, kbArticle: { type: 'string' }, tone: { type: 'string' } },
    },
  ],
  maxTokens: 2048,
  temperature: 0.2,
};
