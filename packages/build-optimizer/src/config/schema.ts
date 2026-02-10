import { z } from 'zod';
import {
  OptimizationConfigSchema,
  AppConfigSchema,
  ThresholdConfigSchema,
  StrategyConfigSchema,
  MonitoringConfigSchema,
} from '../types/config.js';

// Re-export type schemas for convenience
export {
  OptimizationConfigSchema,
  AppConfigSchema,
  ThresholdConfigSchema,
  StrategyConfigSchema,
  MonitoringConfigSchema,
};

// CLI flags schema for parsing command line arguments
export const CliFlagsSchema = z.object({
  config: z.string().optional(),
  verbose: z.boolean().default(false),
  dryRun: z.boolean().default(false),
  app: z.string().optional(),
  format: z.enum(['json', 'table', 'compact']).default('table'),
});

export type CliFlags = z.infer<typeof CliFlagsSchema>;

// Partial config schema for file loading
export const PartialConfigSchema = OptimizationConfigSchema.partial();

export type PartialConfig = z.infer<typeof PartialConfigSchema>;
