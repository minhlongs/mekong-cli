/** Finance data persistence — JSON file store with atomic writes */
import { readFile, writeFile, rename, copyFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { z } from 'zod';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import { InvoiceSchema, ExpenseSchema, RevenueEntrySchema } from './types.js';
import type { Invoice, Expense, RevenueEntry } from './types.js';

const MAX_RECORDS = 10_000;
const BASE_PATH = join(homedir(), '.mekong', 'finance');

type CollectionName = 'invoices' | 'expenses' | 'revenue';
type CollectionType = {
  invoices: Invoice;
  expenses: Expense;
  revenue: RevenueEntry;
};

const SCHEMAS: { [K in CollectionName]: z.ZodSchema<CollectionType[K]> } = {
  invoices: InvoiceSchema as z.ZodSchema<Invoice>,
  expenses: ExpenseSchema as z.ZodSchema<Expense>,
  revenue: RevenueEntrySchema as z.ZodSchema<RevenueEntry>,
};

export class FinanceStore {
  private basePath: string;

  constructor(basePath: string = BASE_PATH) {
    this.basePath = basePath;
  }

  private filePath(collection: CollectionName): string {
    return join(this.basePath, `${collection}.json`);
  }

  private async ensureDir(): Promise<void> {
    await mkdir(this.basePath, { recursive: true });
  }

  private async readAll<K extends CollectionName>(collection: K): Promise<CollectionType[K][]> {
    const path = this.filePath(collection);
    if (!existsSync(path)) return [];
    const raw = await readFile(path, 'utf-8');
    return JSON.parse(raw) as CollectionType[K][];
  }

  private async atomicWrite<K extends CollectionName>(
    collection: K,
    records: CollectionType[K][],
  ): Promise<void> {
    await this.ensureDir();
    const path = this.filePath(collection);
    const tmp = path + '.tmp';
    await writeFile(tmp, JSON.stringify(records, null, 2), 'utf-8');
    await rename(tmp, path);
  }

  private async backup(collection: CollectionName): Promise<void> {
    const path = this.filePath(collection);
    if (existsSync(path)) await copyFile(path, path + '.bak');
  }

  async getAll<K extends CollectionName>(
    collection: K,
    filter?: Partial<CollectionType[K]>,
  ): Promise<Result<CollectionType[K][]>> {
    try {
      let records = await this.readAll(collection);
      if (filter) {
        records = records.filter((r) =>
          Object.entries(filter).every(([k, v]) => (r as Record<string, unknown>)[k] === v),
        );
      }
      return ok(records);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async getById<K extends CollectionName>(
    collection: K,
    id: string,
  ): Promise<Result<CollectionType[K] | null>> {
    try {
      const records = await this.readAll(collection);
      return ok(records.find((r) => (r as { id: string }).id === id) ?? null);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async save<K extends CollectionName>(
    collection: K,
    record: CollectionType[K],
  ): Promise<Result<CollectionType[K]>> {
    try {
      const parsed = SCHEMAS[collection].safeParse(record);
      if (!parsed.success) return err(new Error(`Validation failed: ${parsed.error.message}`));
      const validated = parsed.data as CollectionType[K];
      const records = await this.readAll(collection);
      const idx = records.findIndex((r) => (r as { id: string }).id === (validated as { id: string }).id);
      if (idx >= 0) {
        records[idx] = validated;
      } else {
        if (records.length >= MAX_RECORDS) {
          return err(new Error(`Max records (${MAX_RECORDS}) reached for ${collection}`));
        }
        records.push(validated);
      }
      await this.atomicWrite(collection, records);
      return ok(validated);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async delete<K extends CollectionName>(collection: K, id: string): Promise<Result<boolean>> {
    try {
      await this.backup(collection);
      const records = await this.readAll(collection);
      const filtered = records.filter((r) => (r as { id: string }).id !== id);
      if (filtered.length === records.length) return ok(false);
      await this.atomicWrite(collection, filtered);
      return ok(true);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async nextInvoiceNumber(): Promise<Result<string>> {
    try {
      const records = await this.readAll('invoices');
      const prefix = `INV-${new Date().getFullYear()}-`;
      const nums = records
        .filter((inv) => inv.number.startsWith(prefix))
        .map((inv) => parseInt(inv.number.slice(prefix.length), 10) || 0);
      const next = nums.length > 0 ? Math.max(...nums) + 1 : 1;
      return ok(`${prefix}${String(next).padStart(3, '0')}`);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async getInvoices(filter?: { status?: Invoice['status']; customerId?: string }): Promise<Result<Invoice[]>> {
    try {
      const records = await this.readAll('invoices');
      return ok(records.filter((inv) =>
        (!filter?.status || inv.status === filter.status) &&
        (!filter?.customerId || inv.customerId === filter.customerId),
      ));
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async getExpenses(filter?: { category?: Expense['category']; from?: string; to?: string }): Promise<Result<Expense[]>> {
    try {
      const records = await this.readAll('expenses');
      return ok(records.filter((exp) =>
        (!filter?.category || exp.category === filter.category) &&
        (!filter?.from || exp.date >= filter.from) &&
        (!filter?.to || exp.date <= filter.to),
      ));
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async getRevenue(filter?: { from?: string; to?: string; type?: RevenueEntry['type'] }): Promise<Result<RevenueEntry[]>> {
    try {
      const records = await this.readAll('revenue');
      return ok(records.filter((rev) =>
        (!filter?.type || rev.type === filter.type) &&
        (!filter?.from || rev.date >= filter.from) &&
        (!filter?.to || rev.date <= filter.to),
      ));
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
