import { AppConfig } from '../types/index.js';
import { Logger } from '../types/index.js';

/**
 * Strategy interface for optimization strategies.
 * Implemented in Phase 03.
 */
export interface Strategy {
  readonly name: string;
  readonly description: string;
  
  /**
   * Check if this strategy can be applied to the given app
   */
  canApply(app: AppConfig): Promise<boolean>;
  
  /**
   * Apply the optimization strategy
   */
  apply(app: AppConfig, logger: Logger): Promise<void>;
  
  /**
   * Rollback the optimization if something goes wrong
   */
  rollback(app: AppConfig, logger: Logger): Promise<void>;
}

/**
 * Base strategy class with common functionality
 */
export abstract class BaseStrategy implements Strategy {
  abstract readonly name: string;
  abstract readonly description: string;
  
  abstract canApply(app: AppConfig): Promise<boolean>;
  abstract apply(app: AppConfig, logger: Logger): Promise<void>;
  abstract rollback(app: AppConfig, logger: Logger): Promise<void>;
  
  protected async hasPackageJson(app: AppConfig): Promise<boolean> {
    try {
      const { fileExists } = await import('../utils/fs.js');
      const { join } = await import('path');
      return await fileExists(join(app.path, 'package.json'));
    } catch {
      return false;
    }
  }
  
  protected async readPackageJson(app: AppConfig): Promise<Record<string, unknown> | null> {
    try {
      const { readJson } = await import('../utils/fs.js');
      const { join } = await import('path');
      return await readJson(join(app.path, 'package.json'));
    } catch {
      return null;
    }
  }
}
