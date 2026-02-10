import { cosmiconfig, type CosmiconfigResult } from 'cosmiconfig';
import { z } from 'zod';
import type { OptimizationConfig, PartialConfig } from '../types/index.js';
import { OptimizationConfigSchema, CliFlagsSchema } from './schema.js';
import { defaultConfig } from './defaults.js';

const explorer = cosmiconfig('mekong');

/**
 * Load configuration from multiple sources with priority:
 * 1. CLI flags
 * 2. Environment variables
 * 3. Local config file
 * 4. Global config file
 * 5. Default values
 */
export async function loadConfig(flags: unknown): Promise<OptimizationConfig> {
  // Validate CLI flags
  const cliFlags = CliFlagsSchema.parse(flags);
  
  // Load from file if specified, otherwise search for config
  let fileConfig: PartialConfig = {};
  
  if (cliFlags.config) {
    const result = await explorer.load(cliFlags.config);
    fileConfig = extractConfig(result);
  } else {
    const result = await explorer.search();
    fileConfig = extractConfig(result);
  }
  
  // Get environment-based config
  const envConfig = getEnvConfig();
  
  // Merge configurations: defaults < file < env < flags
  const merged = mergeConfigs(defaultConfig, fileConfig, envConfig);
  
  // Validate final config
  return OptimizationConfigSchema.parse(merged);
}

/**
 * Extract config from cosmiconfig result
 */
function extractConfig(result: CosmiconfigResult): PartialConfig {
  if (!result?.config) return {};
  
  // Support both direct config and nested optimization property
  const config = result.config;
  if (config.optimization && typeof config.optimization === 'object') {
    return config.optimization as PartialConfig;
  }
  
  return config as PartialConfig;
}

/**
 * Get configuration from environment variables
 */
function getEnvConfig(): PartialConfig {
  const env = process.env;
  
  const config: PartialConfig = {};
  
  // Monitoring config
  if (env.MEKONG_MONITORING_ENABLED !== undefined || env.MEKONG_MONITORING_ENDPOINT !== undefined) {
    config.monitoring = {
      enabled: env.MEKONG_MONITORING_ENABLED !== 'false',
      endpoint: env.MEKONG_MONITORING_ENDPOINT,
    };
  }
  
  // Strategy config
  if (
    env.MEKONG_TREE_SHAKING !== undefined ||
    env.MEKONG_CODE_SPLITTING !== undefined ||
    env.MEKONG_COMPRESSION !== undefined ||
    env.MEKONG_CACHING !== undefined
  ) {
    config.strategies = {
      treeShaking: env.MEKONG_TREE_SHAKING !== 'false',
      codeSplitting: env.MEKONG_CODE_SPLITTING !== 'false',
      compression: env.MEKONG_COMPRESSION !== 'false',
      caching: env.MEKONG_CACHING !== 'false',
    };
  }
  
  // Threshold config
  if (
    env.MEKONG_BUNDLE_SIZE_WARNING !== undefined ||
    env.MEKONG_BUNDLE_SIZE_ERROR !== undefined ||
    env.MEKONG_BUILD_TIME_WARNING !== undefined ||
    env.MEKONG_BUILD_TIME_ERROR !== undefined
  ) {
    config.thresholds = {
      bundleSizeWarning: parseInt(env.MEKONG_BUNDLE_SIZE_WARNING || '400', 10),
      bundleSizeError: parseInt(env.MEKONG_BUNDLE_SIZE_ERROR || '600', 10),
      buildTimeWarning: parseInt(env.MEKONG_BUILD_TIME_WARNING || '90', 10),
      buildTimeError: parseInt(env.MEKONG_BUILD_TIME_ERROR || '180', 10),
    };
  }
  
  return config;
}

/**
 * Merge multiple configuration objects
 */
function mergeConfigs(
  defaults: OptimizationConfig,
  file: PartialConfig,
  env: PartialConfig
): OptimizationConfig {
  return {
    ...defaults,
    ...file,
    ...env,
    thresholds: {
      ...defaults.thresholds,
      ...file.thresholds,
      ...env.thresholds,
    },
    strategies: {
      ...defaults.strategies,
      ...file.strategies,
      ...env.strategies,
    },
    monitoring: {
      ...defaults.monitoring,
      ...file.monitoring,
      ...env.monitoring,
    },
  };
}

/**
 * Validate a configuration object
 */
export function validateConfig(config: unknown): OptimizationConfig {
  return OptimizationConfigSchema.parse(config);
}

/**
 * Get a specific app configuration by name
 */
export function getAppConfig(
  config: OptimizationConfig,
  appName: string
): import('../types/config.js').AppConfig | undefined {
  return config.apps.find(app => app.name === appName);
}
