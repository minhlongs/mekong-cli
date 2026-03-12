/** CRM data persistence — JSON file store with atomic writes */
import { readFile, writeFile, rename, copyFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { z } from 'zod';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import { LeadSchema, CustomerSchema, TicketSchema } from './types.js';
import type { Lead, Customer, Ticket } from './types.js';

const MAX_RECORDS = 10_000;
const BASE_PATH = join(homedir(), '.mekong', 'crm');

type CollectionName = 'leads' | 'customers' | 'tickets';
type CollectionType = {
  leads: Lead;
  customers: Customer;
  tickets: Ticket;
};

const SCHEMAS: { [K in CollectionName]: z.ZodSchema<CollectionType[K]> } = {
  leads: LeadSchema as z.ZodSchema<Lead>,
  customers: CustomerSchema as z.ZodSchema<Customer>,
  tickets: TicketSchema as z.ZodSchema<Ticket>,
};

export class CrmStore {
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
    if (existsSync(path)) {
      await copyFile(path, path + '.bak');
    }
  }

  /** Get all records, optionally filtered */
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

  /** Get single record by id */
  async getById<K extends CollectionName>(
    collection: K,
    id: string,
  ): Promise<Result<CollectionType[K] | null>> {
    try {
      const records = await this.readAll(collection);
      const found = records.find((r) => (r as { id: string }).id === id) ?? null;
      return ok(found);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Save (upsert) a record with Zod validation */
  async save<K extends CollectionName>(
    collection: K,
    record: CollectionType[K],
  ): Promise<Result<CollectionType[K]>> {
    try {
      const parsed = SCHEMAS[collection].safeParse(record);
      if (!parsed.success) {
        return err(new Error(`Validation failed: ${parsed.error.message}`));
      }
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

  /** Delete a record by id (with backup) */
  async delete<K extends CollectionName>(
    collection: K,
    id: string,
  ): Promise<Result<boolean>> {
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

  /** Delete all records (with backup) */
  async deleteAll(collection: CollectionName): Promise<Result<void>> {
    try {
      await this.backup(collection);
      await this.atomicWrite(collection, []);
      return ok(undefined);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
