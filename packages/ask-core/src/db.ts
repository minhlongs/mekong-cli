import { Database, Statement } from 'bun:sqlite';
import { join, dirname } from 'path';
import { homedir } from 'os';
import { mkdirSync, existsSync } from 'fs';

export interface Chunk {
  id: string; // unique chunk ID (e.g. SHA-256 of filePath + content / headers)
  filePath: string;
  title: string;
  content: string;
  h1: string | null;
  h2: string | null;
  h3: string | null;
  h4: string | null;
  parentHeaders: string[];
}

export interface SearchResult extends Chunk {
  rank: number;
  updatedAt: string;
}

export const DEFAULT_DB_DIR = join(homedir(), '.mekong', 'ask');
export const DEFAULT_DB_PATH = join(DEFAULT_DB_DIR, 'ask.db');

export class AskDatabase {
  private db: Database;
  private dbPath: string;
  private stmtDeleteChunks!: Statement;
  private stmtDeleteFts!: Statement;
  private stmtInsertChunk!: Statement;
  private stmtInsertFts!: Statement;
  private stmtSearch!: Statement;
  private stmtInsertVector!: Statement;
  private stmtDeleteVectors!: Statement;
  private stmtGetAllVectors!: Statement;
  private stmtGetChunkById!: Statement;

  constructor(dbPath: string = DEFAULT_DB_PATH) {
    this.dbPath = dbPath;
    const dir = dirname(dbPath);
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
    this.db = new Database(dbPath);
    this.db.exec('PRAGMA journal_mode = WAL;');
    this.init();
    this.prepareStatements();
  }

  /**
   * Initializes the SQLite schema and FTS5 virtual table.
   */
  public init(): void {
    // 1. Create the chunks metadata table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY,
        file_path TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        h1 TEXT,
        h2 TEXT,
        h3 TEXT,
        h4 TEXT,
        parent_headers TEXT, -- JSON array of strings
        updated_at TEXT NOT NULL
      );

      CREATE INDEX IF NOT EXISTS idx_chunks_file_path ON chunks(file_path);
    `);

    // 2. Create the FTS5 virtual table
    this.db.exec(`
      CREATE VIRTUAL TABLE IF NOT EXISTS fts_index USING fts5(
        title,
        content,
        file_path,
        chunk_id
      );
    `);

    // 3. Create the chunk vectors table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS chunk_vectors (
        chunk_id TEXT PRIMARY KEY,
        file_path TEXT NOT NULL,
        vector TEXT NOT NULL, -- JSON array of floats
        FOREIGN KEY(chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
      );
      CREATE INDEX IF NOT EXISTS idx_vectors_file_path ON chunk_vectors(file_path);
    `);
  }

  /**
   * Pre-compiles SQL statements to improve performance.
   */
  private prepareStatements(): void {
    this.stmtDeleteChunks = this.db.prepare('DELETE FROM chunks WHERE file_path = ?');
    this.stmtDeleteFts = this.db.prepare('DELETE FROM fts_index WHERE file_path = ?');
    this.stmtInsertChunk = this.db.prepare(`
      INSERT INTO chunks (id, file_path, title, content, h1, h2, h3, h4, parent_headers, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    this.stmtInsertFts = this.db.prepare(`
      INSERT INTO fts_index (title, content, file_path, chunk_id)
      VALUES (?, ?, ?, ?)
    `);
    this.stmtSearch = this.db.prepare(`
      SELECT f.chunk_id as id, f.file_path as filePath, f.title, f.content,
             c.h1, c.h2, c.h3, c.h4, c.parent_headers as parentHeadersJson,
             c.updated_at as updatedAt, rank
      FROM fts_index f
      JOIN chunks c ON f.chunk_id = c.id
      WHERE fts_index MATCH ?
      ORDER BY rank
      LIMIT ?
    `);
    this.stmtInsertVector = this.db.prepare(`
      INSERT OR REPLACE INTO chunk_vectors (chunk_id, file_path, vector)
      VALUES (?, ?, ?)
    `);
    this.stmtDeleteVectors = this.db.prepare('DELETE FROM chunk_vectors WHERE file_path = ?');
    this.stmtGetAllVectors = this.db.prepare(`
      SELECT cv.chunk_id as chunkId, cv.file_path as filePath, cv.vector as vectorJson,
             c.title, c.content, c.h1, c.h2, c.h3, c.h4, c.parent_headers as parentHeadersJson
      FROM chunk_vectors cv
      JOIN chunks c ON cv.chunk_id = c.id
    `);
    this.stmtGetChunkById = this.db.prepare(`
      SELECT id, file_path as filePath, title, content, h1, h2, h3, h4, parent_headers as parentHeadersJson
      FROM chunks
      WHERE id = ?
    `);
  }

  /**
   * Cleans up all indexed chunks and search indexes for a specific file.
   */
  public deleteFile(filePath: string): void {
    const transaction = this.db.transaction(() => {
      this.stmtDeleteChunks.run(filePath);
      this.stmtDeleteFts.run(filePath);
      this.stmtDeleteVectors.run(filePath);
    });

    transaction();
  }

  /**
   * Indexes a list of chunks for a file. Old chunks for the same file are deleted first.
   */
  public indexChunks(filePath: string, chunks: Chunk[]): void {
    const updatedAt = new Date().toISOString();

    const transaction = this.db.transaction(() => {
      // Clear existing chunks for this file to ensure clean updates
      this.stmtDeleteChunks.run(filePath);
      this.stmtDeleteFts.run(filePath);
      this.stmtDeleteVectors.run(filePath);

      // Insert new chunks
      for (const chunk of chunks) {
        this.stmtInsertChunk.run(
          chunk.id,
          chunk.filePath,
          chunk.title,
          chunk.content,
          chunk.h1,
          chunk.h2,
          chunk.h3,
          chunk.h4,
          JSON.stringify(chunk.parentHeaders),
          updatedAt
        );

        this.stmtInsertFts.run(
          chunk.title,
          chunk.content,
          chunk.filePath,
          chunk.id
        );
      }
    });

    transaction();
  }

  /**
   * Saves a chunk's dense embedding vector.
   */
  public saveVector(chunkId: string, filePath: string, vector: number[]): void {
    this.stmtInsertVector.run(chunkId, filePath, JSON.stringify(vector));
  }

  /**
   * Retrieves all stored vectors with their matching chunks.
   */
  public getAllVectors(): Array<{
    chunkId: string;
    filePath: string;
    vector: number[];
    chunk: Chunk;
  }> {
    const rows = this.stmtGetAllVectors.all() as Array<{
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
    }>;

    return rows.map(row => {
      let vector: number[] = [];
      let parentHeaders: string[] = [];
      try {
        vector = JSON.parse(row.vectorJson);
        parentHeaders = JSON.parse(row.parentHeadersJson);
      } catch (e) {
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
          parentHeaders
        }
      };
    });
  }

  /**
   * Gets a specific chunk by its ID.
   */
  public getChunkById(id: string): Chunk | null {
    const row = this.stmtGetChunkById.get(id) as {
      id: string;
      filePath: string;
      title: string;
      content: string;
      h1: string | null;
      h2: string | null;
      h3: string | null;
      h4: string | null;
      parentHeadersJson: string;
    } | null;

    if (!row) return null;

    let parentHeaders: string[] = [];
    try {
      parentHeaders = JSON.parse(row.parentHeadersJson);
    } catch (e) {
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
      parentHeaders
    };
  }

  /**
   * Helper to sanitize search query for FTS5 syntax, escaping special characters
   * or wrapping terms with hyphens/spaces/colons in double quotes to prevent syntax errors.
   */
  private sanitizeFtsQuery(query: string): string {
    const terms = query.trim().split(/\s+/);
    return terms
      .map(term => {
        if (!term) return '';
        if (term.startsWith('"') && term.endsWith('"')) {
          return term;
        }
        const clean = term.replace(/"/g, '""');
        if (clean.includes('-') || clean.includes(':') || clean.includes('/') || clean.includes('\\')) {
          return `"${clean}"`;
        }
        return clean;
      })
      .filter(t => t.length > 0)
      .join(' ');
  }

  /**
   * Performs full-text search against the index.
   */
  public search(query: string, limit: number = 10): SearchResult[] {
    // If the query is empty, return empty results
    if (!query.trim()) {
      return [];
    }

    const sanitizedQuery = this.sanitizeFtsQuery(query);
    if (!sanitizedQuery) {
      return [];
    }

    try {
      const rows = this.stmtSearch.all(sanitizedQuery, limit) as Array<{
        id: string;
        filePath: string;
        title: string;
        content: string;
        h1: string | null;
        h2: string | null;
        h3: string | null;
        h4: string | null;
        parentHeadersJson: string;
        updatedAt: string;
        rank: number;
      }>;

      return rows.map(row => {
        let parentHeaders: string[] = [];
        try {
          parentHeaders = JSON.parse(row.parentHeadersJson);
        } catch (e) {
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
          updatedAt: row.updatedAt
        };
      });
    } catch (e) {
      console.error(`FTS search failed for query "${query}":`, e);
      return [];
    }
  }

  /**
   * Closes the database connection.
   */
  public close(): void {
    this.db.close();
  }
}
