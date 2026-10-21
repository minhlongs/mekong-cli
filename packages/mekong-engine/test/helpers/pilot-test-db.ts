import type { D1Database } from '@cloudflare/workers-types'
import {
  executePilotAll,
  executePilotFirst,
  type CreditEventRow,
  type CreditRow,
  type FeedbackRow,
  type InMemoryPilotDbState,
  type OutboxRow,
} from './pilot-test-db-queries'
import { executePilotRun } from './pilot-test-db-mutations'

export type { CreditEventRow, CreditRow, FeedbackRow, InMemoryPilotDbState, OutboxRow }

export function createInMemoryPilotDb(): { db: D1Database; state: InMemoryPilotDbState } {
  const state: InMemoryPilotDbState = {
    invites: [],
    tenants: [],
    credits: [],
    creditEvents: [],
    missions: [],
    outbox: [],
    feedback: [],
    statusHistory: [],
  }
  let creditIdCounter = 1

  const prepare = (sql: string) => {
    let boundArgs: unknown[] = []
    const stmt = {
      bind: (...args: unknown[]) => {
        boundArgs = args
        return stmt
      },
      first: <T = unknown>(): Promise<T | null> => executePilotFirst<T>(sql, boundArgs, state),
      all: <T = unknown>(): Promise<{ results: T[] }> => executePilotAll<T>(sql, boundArgs, state),
      run: () => executePilotRun(sql, boundArgs, state, () => creditIdCounter++),
    }
    return stmt
  }

  const db = {
    prepare,
    exec: async () => ({ count: 1, duration: 0 }),
    batch: async (statements: Array<{ run: () => Promise<unknown> }>) => {
      const results = []
      for (const s of statements) {
        results.push(await s.run())
      }
      return results
    },
  } as unknown as D1Database

  return { db, state }
}

export const createPilotD1 = createInMemoryPilotDb
