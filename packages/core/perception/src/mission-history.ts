import * as fs from 'fs/promises';
import * as path from 'path';
import { MissionResult } from './types';

export class MissionHistory {
  private dbPath: string;

  constructor(dbPath: string) {
    this.dbPath = dbPath;
  }

  async save(result: MissionResult): Promise<void> {
    const history = await this.load();
    history.push(result);
    await this.saveToFile(history);
  }

  async load(): Promise<MissionResult[]> {
    try {
      const content = await fs.readFile(this.dbPath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      if ((error as any).code === 'ENOENT') {
        return [];
      }
      throw error;
    }
  }

  async getRecentFailures(limit: number = 5): Promise<MissionResult[]> {
    const history = await this.load();
    return history
      .filter(m => !m.success)
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  }

  async getStats(): Promise<{ total: number; success: number; failure: number; successRate: number }> {
    const history = await this.load();
    const total = history.length;
    const success = history.filter(m => m.success).length;
    const failure = total - success;
    
    return {
      total,
      success,
      failure,
      successRate: total > 0 ? (success / total) * 100 : 0
    };
  }

  private async saveToFile(history: MissionResult[]): Promise<void> {
    await fs.mkdir(path.dirname(this.dbPath), { recursive: true });
    await fs.writeFile(this.dbPath, JSON.stringify(history, null, 2));
  }
}
