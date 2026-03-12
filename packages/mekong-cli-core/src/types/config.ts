import { z } from 'zod';

export const ConfigSchema = z.object({
  version: z.string().default('1'),
  llm: z.object({
    default_provider: z.enum(['anthropic', 'openai', 'deepseek', 'ollama']).default('anthropic'),
    default_model: z.string().default('claude-sonnet-4-20250514'),
    providers: z.record(z.object({
      api_key: z.string().optional(),
      api_key_env: z.string().optional(),
      base_url: z.string().optional(),
      default_model: z.string().optional(),
    })).default({}),
  }).default({}),
  agents: z.object({
    max_iterations: z.number().default(10),
    max_tokens_per_turn: z.number().default(4096),
    wip_limit: z.number().default(3),
    timeout_seconds: z.number().default(300),
  }).default({}),
  budget: z.object({
    max_cost_per_task: z.number().default(1.0),
    max_tokens_per_task: z.number().default(100000),
    warn_at_percent: z.number().default(80),
  }).default({}),
  tools: z.object({
    auto_approve_level: z.enum(['0', '1', '2', '3']).default('1'),
    sandbox_shell: z.boolean().default(true),
    allowed_directories: z.array(z.string()).default(['./']),
    blocked_commands: z.array(z.string()).default(['rm -rf /', 'sudo']),
  }).default({}),
  heartbeat: z.object({
    enabled: z.boolean().default(false),
    interval_minutes: z.number().default(30),
    checklist_file: z.string().default('HEARTBEAT.md'),
  }).default({}),
  memory: z.object({
    session_dir: z.string().default('~/.mekong/sessions'),
    knowledge_dir: z.string().default('~/.mekong/knowledge'),
    max_session_size_mb: z.number().default(10),
    auto_compact: z.boolean().default(true),
  }).default({}),
});

export type MekongConfig = z.infer<typeof ConfigSchema>;
