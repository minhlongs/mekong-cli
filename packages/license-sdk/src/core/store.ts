import { mkdirSync, readFileSync, writeFileSync, unlinkSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import type { Brand } from './tiers.js';
import type { LicenseKey } from './key-generator.js';

const STORE_DIR = join(homedir(), '.openclaw', 'licenses');

function ensureDir(): void {
  mkdirSync(STORE_DIR, { recursive: true });
}

function filePath(brand: Brand): string {
  return join(STORE_DIR, `${brand}.json`);
}

export class LicenseStore {
  private readonly dir: string;

  constructor(storeDir?: string) {
    this.dir = storeDir ?? STORE_DIR;
  }

  private ensureDir(): void {
    mkdirSync(this.dir, { recursive: true });
  }

  private filePath(brand: Brand): string {
    return join(this.dir, `${brand}.json`);
  }

  save(brand: Brand, key: LicenseKey): void {
    this.ensureDir();
    writeFileSync(this.filePath(brand), JSON.stringify(key, null, 2), 'utf-8');
  }

  load(brand: Brand): LicenseKey | null {
    try {
      const raw = readFileSync(this.filePath(brand), 'utf-8');
      return JSON.parse(raw) as LicenseKey;
    } catch {
      return null;
    }
  }

  remove(brand: Brand): boolean {
    try {
      unlinkSync(this.filePath(brand));
      return true;
    } catch {
      return false;
    }
  }

  listAll(): { brand: Brand; key: LicenseKey }[] {
    try {
      this.ensureDir();
      const files = readdirSync(this.dir).filter((f) => f.endsWith('.json'));
      const results: { brand: Brand; key: LicenseKey }[] = [];
      for (const file of files) {
        try {
          const raw = readFileSync(join(this.dir, file), 'utf-8');
          const key = JSON.parse(raw) as LicenseKey;
          results.push({ brand: key.brand, key });
        } catch {
          // skip corrupt files
        }
      }
      return results;
    } catch {
      return [];
    }
  }
}

// Singleton default store
export const defaultStore = new LicenseStore();

// Keep ensureDir / filePath exports for potential direct use
export { ensureDir, filePath };
