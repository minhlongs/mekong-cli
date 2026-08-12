/**
 * Content Writer Agent — SEO content and copywriting for AI/RaaS audience
 * Routes to Qwen2.5-Coder-32B (planning) for structured creative output
 */

import type { AgentDefinition } from './types.js';

export const contentWriterAgent: AgentDefinition = {
  id: 'content-writer',
  name: 'Content Writer',
  description: 'Writes SEO blog posts, email sequences, and social content for AI/RaaS audiences',
  capability: 'content-creation',
  modelPreference: 'planning',
  systemPrompt:
    'Write compelling content targeting AI-native and RaaS (Robots-as-a-Service) buyers. ' +
    'For blog posts, structure with SEO-optimized H2/H3 hierarchy and a clear CTA. ' +
    'For email sequences, maintain consistent voice across touches and personalize by industry vertical. ' +
    'For social posts, lead with a strong hook and keep copy scannable. ' +
    'Always align messaging to business value — cost savings, time-to-value, and competitive advantage.',
  tools: [
    {
      name: 'keyword_research',
      description: 'Find high-value SEO keywords for a given topic and audience',
      parameters: { topic: { type: 'string' }, audience: { type: 'string' } },
    },
    {
      name: 'content_outline',
      description: 'Generate a structured content outline with headings and key points',
      parameters: { title: { type: 'string' }, keywords: { type: 'array' }, format: { type: 'string' } },
    },
    {
      name: 'seo_optimize',
      description: 'Analyze and improve SEO score of drafted content',
      parameters: { content: { type: 'string' }, targetKeyword: { type: 'string' } },
    },
  ],
  maxTokens: 8192,
  temperature: 0.7,
};
