import * as yaml from 'yaml';
import * as fs from 'fs';
import * as path from 'path';
import { IConfig } from '../interfaces/IConfig';

import { logger } from './logger';

export class ConfigLoader {
  private static config: IConfig;

  static load(configPath: string = 'config/default.yaml'): IConfig {
    if (this.config) return this.config;

    try {
      const file = fs.readFileSync(path.resolve(process.cwd(), configPath), 'utf8');
      this.config = yaml.parse(file) as IConfig;

      // Override with env vars if needed
      if (process.env.API_KEY) this.config.exchange.apiKey = process.env.API_KEY;
      if (process.env.API_SECRET) this.config.exchange.secret = process.env.API_SECRET;

      return this.config;
    } catch (e) {
      logger.error(`Failed to load config from ${configPath}: ${e instanceof Error ? e.message : String(e)}`);
      throw e;
    }
  }

  static get(): IConfig {
    if (!this.config) {
      return this.load();
    }
    return this.config;
  }
}
