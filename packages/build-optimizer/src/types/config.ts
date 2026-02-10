import { z } from 'zod';

// App configuration schema
export const AppConfigSchema = z.object({
  name: z.string(),
  path: z.string(),
  type: z.enum(['nextjs', 'vite', 'webpack', 'node']),
  buildCommand: z.string().default('npm run build'),
  outputDir: z.string().default('dist'),
  budget: z.object({
    maxBundleSize: z.number().default(500),
    maxBuildTime: z.number().default(120),
  }).optional(),
});

// Threshold configuration schema
export const ThresholdConfigSchema = z.object({
  bundleSizeWarning: z.number().default(400),
  bundleSizeError: z.number().default(600),
  buildTimeWarning: z.number().default(90),
  buildTimeError: z.number().default(180),
});

// Strategy configuration schema
export const StrategyConfigSchema = z.object({
  treeShaking: z.boolean().default(true),
  codeSplitting: z.boolean().default(true),
  compression: z.boolean().default(true),
  caching: z.boolean().default(true),
});

// Monitoring configuration schema
export const MonitoringConfigSchema = z.object({
  enabled: z.boolean().default(true),
  endpoint: z.string().optional(),
});

// Main optimization configuration schema
export const OptimizationConfigSchema = z.object({
  apps: z.array(AppConfigSchema),
  thresholds: ThresholdConfigSchema,
  strategies: StrategyConfigSchema,
  monitoring: MonitoringConfigSchema,
});

// Inferred types
export type AppConfig = z.infer<typeof AppConfigSchema>;
export type ThresholdConfig = z.infer<typeof ThresholdConfigSchema>;
export type StrategyConfig = z.infer<typeof StrategyConfigSchema>;
export type MonitoringConfig = z.infer<typeof MonitoringConfigSchema>;
export type OptimizationConfig = z.infer<typeof OptimizationConfigSchema>;

// Partial config type for merging
export type PartialConfig = Partial<Omit<OptimizationConfig, 'thresholds' | 'strategies' | 'monitoring'>> & {
  thresholds?: Partial<ThresholdConfig>;
  strategies?: Partial<StrategyConfig>;
  monitoring?: Partial<MonitoringConfig>;
};
