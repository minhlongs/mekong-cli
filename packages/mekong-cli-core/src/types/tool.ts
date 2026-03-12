import { z } from 'zod';
import type { Result } from './common.js';

/** Security approval level required to run the tool */
export type SecurityLevel = 0 | 1 | 2 | 3;

export const ToolParamSchema = z.object({
  name: z.string(),
  type: z.enum(['string', 'number', 'boolean', 'object', 'array']),
  required: z.boolean().default(true),
  description: z.string(),
  default: z.unknown().optional(),
  enum: z.array(z.string()).optional(),
});

export type ToolParam = z.infer<typeof ToolParamSchema>;

export interface ToolDefinition {
  name: string;
  description: string;
  category: 'filesystem' | 'shell' | 'network' | 'llm' | 'memory' | 'custom';
  securityLevel: SecurityLevel;
  params: ToolParam[];
  execute: (params: Record<string, unknown>) => Promise<ToolResult>;
}

export interface ToolResult {
  success: boolean;
  output: unknown;
  error?: string;
  metadata?: Record<string, unknown>;
}

/** Wrap tool execution in Result type */
export type ToolExecuteResult = Result<ToolResult>;
