import { z } from 'zod';
import type { Id, Status, Timestamp } from './common.js';

export const SopInputSchema = z.object({
  name: z.string(),
  type: z.enum(['string', 'number', 'boolean', 'object', 'array']),
  required: z.boolean().default(true),
  description: z.string().optional(),
  default: z.unknown().optional(),
});

export const SopPreconditionSchema = z.object({
  type: z.enum(['file_exists', 'env_set', 'command_available', 'custom']),
  value: z.string(),
  message: z.string().optional(),
});

export const SopStepSchema = z.object({
  id: z.string(),
  name: z.string(),
  action: z.enum(['shell', 'llm', 'tool', 'agent', 'sop', 'condition']),
  command: z.string().optional(),
  prompt: z.string().optional(),
  tool: z.string().optional(),
  sop: z.string().optional(),
  inputs: z.record(z.unknown()).optional(),
  outputs: z.array(z.string()).optional(),
  condition: z.string().optional(),
  on_success: z.string().optional(),
  on_failure: z.enum(['stop', 'continue', 'retry']).default('stop'),
  retry: z.object({
    max: z.number().default(3),
    delay_seconds: z.number().default(5),
  }).optional(),
  timeout_seconds: z.number().optional(),
});

export const SopDefinitionSchema = z.object({
  sop: z.object({
    name: z.string(),
    version: z.string().default('1.0.0'),
    description: z.string().optional(),
    author: z.string().optional(),
    tags: z.array(z.string()).default([]),
    inputs: z.array(SopInputSchema).default([]),
    preconditions: z.array(SopPreconditionSchema).default([]),
    steps: z.array(SopStepSchema),
    outputs: z.record(z.string()).optional(),
  }),
});

export type SopDefinition = z.infer<typeof SopDefinitionSchema>;
export type SopStep = z.infer<typeof SopStepSchema>;
export type SopInput = z.infer<typeof SopInputSchema>;

export interface StepState {
  stepId: Id;
  status: Status;
  startedAt: Timestamp;
  completedAt?: Timestamp;
  output?: unknown;
  error?: string;
  retryCount: number;
}

export interface SopRun {
  id: Id;
  sopName: string;
  sopVersion: string;
  status: Status;
  startedAt: Timestamp;
  completedAt?: Timestamp;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  steps: StepState[];
  error?: string;
}
