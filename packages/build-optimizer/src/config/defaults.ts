import type { OptimizationConfig } from '../types/config.js';

// Default configuration values following YAGNI principle
export const defaultConfig: OptimizationConfig = {
  apps: [],
  thresholds: {
    bundleSizeWarning: 400,
    bundleSizeError: 600,
    buildTimeWarning: 90,
    buildTimeError: 180,
  },
  strategies: {
    treeShaking: true,
    codeSplitting: true,
    compression: true,
    caching: true,
  },
  monitoring: {
    enabled: true,
    endpoint: undefined,
  },
};

// Preset configurations for common setups
export const presets = {
  // Conservative settings for legacy projects
  conservative: {
    thresholds: {
      bundleSizeWarning: 600,
      bundleSizeError: 1000,
      buildTimeWarning: 120,
      buildTimeError: 240,
    },
    strategies: {
      treeShaking: false,
      codeSplitting: true,
      compression: true,
      caching: true,
    },
  },
  
  // Aggressive optimization for new projects
  aggressive: {
    thresholds: {
      bundleSizeWarning: 200,
      bundleSizeError: 400,
      buildTimeWarning: 60,
      buildTimeError: 120,
    },
    strategies: {
      treeShaking: true,
      codeSplitting: true,
      compression: true,
      caching: true,
    },
  },
  
  // Minimal config for CI environments
  minimal: {
    monitoring: {
      enabled: false,
    },
  },
} as const;
