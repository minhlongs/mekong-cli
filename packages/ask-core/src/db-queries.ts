import { Statement } from 'bun:sqlite';
import type { Chunk, SearchResult } from './db-schema';

interface VectorJoinRow {
  chunkId: string;
  filePath: string;
  vectorJson: string;
  title: string;
  content: string;
  h1: string | null;
  h2: string | null;
  h3: string | null;
  h4: string | null;
  parentHeadersJson: string;
}

interface ChunkRow {
  id: string;
  filePath: string;
  title: string;
  content: string;
  h1: string | null;
  h2: string | null;
  h3: string | null;
  h4: string | null;
  parentHeadersJson: string;
}

interface SearchRow extends ChunkRow {
  updatedAt: string;
  rank: number;
}

export function mapAllVectors(stmtGetAllVectors: Statement): Array<{
  chunkId: string;
  filePath: string;
  vector: number[];
  chunk: Chunk;
}> {
  const rows = stmtGetAllVectors.all() as VectorJoinRow[];

  return rows.map((row) => {
    let vector: number[] = [];
    let parentHeaders: string[] = [];
    try {
      vector = JSON.parse(row.vectorJson) as number[];
      parentHeaders = JSON.parse(row.parentHeadersJson) as string[];
    } catch {
      // Fallback
    }

    return {
      chunkId: row.chunkId,
      filePath: row.filePath,
      vector,
      chunk: {
        id: row.chunkId,
        filePath: row.filePath,
        title: row.title,
        content: row.content,
        h1: row.h1,
        h2: row.h2,
        h3: row.h3,
        h4: row.h4,
        parentHeaders,
      },
    };
  });
}

export function mapChunkById(stmtGetChunkById: Statement, id: string): Chunk | null {
  const row = stmtGetChunkById.get(id) as ChunkRow | null;
  if (!row) return null;

  let parentHeaders: string[] = [];
  try {
    parentHeaders = JSON.parse(row.parentHeadersJson) as string[];
  } catch {
    // Fallback
  }

  return {
    id: row.id,
    filePath: row.filePath,
    title: row.title,
    content: row.content,
    h1: row.h1,
    h2: row.h2,
    h3: row.h3,
    h4: row.h4,
    parentHeaders,
  };
}

export function sanitizeFtsQuery(query: string): string {
  const terms = query.trim().split(/\s+/);
  return terms
    .map((term) => {
      if (!term) return '';
      if (term.startsWith('"') && term.endsWith('"')) {
        return term;
      }
      const clean = term.replace(/"/g, '""');
      if (
        clean.includes('-') ||
        clean.includes(':') ||
        clean.includes('/') ||
        clean.includes('\\')
      ) {
        return `"${clean}"`;
      }
      return clean;
    })
    .filter((t) => t.length > 0)
    .join(' ');
}

export function searchFts(
  stmtSearch: Statement,
  query: string,
  limit: number = 10
): SearchResult[] {
  if (!query.trim()) {
    return [];
  }

  const sanitizedQuery = sanitizeFtsQuery(query);
  if (!sanitizedQuery) {
    return [];
  }

  try {
    const rows = stmtSearch.all(sanitizedQuery, limit) as SearchRow[];

    return rows.map((row) => {
      let parentHeaders: string[] = [];
      try {
        parentHeaders = JSON.parse(row.parentHeadersJson) as string[];
      } catch {
        parentHeaders = [];
      }

      return {
        id: row.id,
        filePath: row.filePath,
        title: row.title,
        content: row.content,
        h1: row.h1,
        h2: row.h2,
        h3: row.h3,
        h4: row.h4,
        parentHeaders,
        rank: row.rank,
        updatedAt: row.updatedAt,
      };
    });
  } catch (e) {
    console.error(`FTS search failed for query "${query}":`, e);
    return [];
  }
}
