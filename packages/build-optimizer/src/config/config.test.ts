import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { loadConfig, validateConfig } from './index.js';
import { defaultConfig } from './defaults.js';

describe('config', () => {
  describe('loadConfig', () => {
    it('should load default config when no file exists', async () => {
      const config = await loadConfig({});
      
      expect(config.thresholds.bundleSizeWarning).toBe(defaultConfig.thresholds.bundleSizeWarning);
      expect(config.strategies.treeShaking).toBe(defaultConfig.strategies.treeShaking);
      expect(config.monitoring.enabled).toBe(defaultConfig.monitoring.enabled);
    });
    
    it('should respect CLI flags', async () => {
      const config = await loadConfig({ verbose: true });
      
      // verbose flag doesn't affect config, but should parse without error
      expect(config).toBeDefined();
    });
  });
  
  describe('validateConfig', () => {
    it('should validate a correct config', () => {
      const config = validateConfig(defaultConfig);
      
      expect(config).toEqual(defaultConfig);
    });
    
    it('should throw on invalid config', () => {
      expect(() => {
        validateConfig({ invalid: true });
      }).toThrow();
    });
    
    it('should validate with custom apps', () => {
      const config = validateConfig({
        ...defaultConfig,
        apps: [
          {
            name: 'test-app',
            path: './test',
            type: 'nextjs',
            buildCommand: 'npm run build',
            outputDir: 'dist',
          },
        ],
      });
      
      expect(config.apps).toHaveLength(1);
      expect(config.apps[0].name).toBe('test-app');
    });
  });
});
