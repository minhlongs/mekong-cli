/**
 * Default automation pipelines for solo founder RaaS operations.
 * Three pipelines: lead scanning, content batching, support triage.
 */

import type { Pipeline } from './types.js';

export const DEFAULT_PIPELINES: Pipeline[] = [
  {
    id: 'daily-lead-scan',
    name: 'Daily Lead Scanner',
    schedule: '0 9 * * 1-5',
    agentId: 'lead-hunter',
    inputTemplate:
      'Scan for new prospects in AI automation, SaaS, and digital agency verticals. ' +
      'Score each lead 1-100.',
    enabled: true,
  },
  {
    id: 'content-batch',
    name: 'Content Batch Writer',
    schedule: '0 10 * * 1,3,5',
    agentId: 'content-writer',
    inputTemplate:
      'Write a blog post about {{topic}} targeting {{audience}}. ' +
      'SEO-optimized, 1500-2000 words.',
    enabled: true,
  },
  {
    id: 'support-triage',
    name: 'Support Ticket Triage',
    schedule: '*/30 * * * *',
    agentId: 'support-bot',
    inputTemplate:
      'Triage open support tickets. Classify by severity (critical/high/medium/low). ' +
      'Auto-respond to low-severity with knowledge base solution.',
    enabled: true,
  },
];

/** Look up a default pipeline by id */
export function getDefaultPipeline(id: string): Pipeline | undefined {
  return DEFAULT_PIPELINES.find((p) => p.id === id);
}
