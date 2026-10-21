import { Database, Statement } from 'bun:sqlite';
import { join } from 'path';
import { homedir } from 'os';

export interface Chunk {
  id: string;
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

export interface PreparedStatements {
  stmtDeleteChunks: Statement;
  stmtDeleteFts: Statement;
  stmtInsertChunk: Statement;
  stmtInsertFts: Statement;
  stmtSearch: Statement;
  stmtInsertVector: Statement;
  stmtDeleteVectors: Statement;
  stmtGetAllVectors: Statement;
  stmtGetChunkById: Statement;
}

export const DEFAULT_DB_DIR = join(homedir(), '.mekong', 'ask');
export const DEFAULT_DB_PATH = join(DEFAULT_DB_DIR, 'ask.db');

export function initDatabaseSchema(db: Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS chunks (
      id TEXT PRIMARY KEY,
      file_path TEXT NOT NULL,
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      h1 TEXT,
      h2 TEXT,
      h3 TEXT,
      h4 TEXT,
      parent_headers TEXT,
      updated_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_chunks_file_path ON chunks(file_path);
  `);

  db.exec(`
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_index USING fts5(
      title,
      content,
      file_path,
      chunk_id
    );
  `);

  db.exec(`
    CREATE TABLE IF NOT EXISTS chunk_vectors (
      chunk_id TEXT PRIMARY KEY,
      file_path TEXT NOT NULL,
      vector TEXT NOT NULL,
      FOREIGN KEY(chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_vectors_file_path ON chunk_vectors(file_path);
  `);
}

export function prepareDatabaseStatements(db: Database): PreparedStatements {
  return {
    stmtDeleteChunks: db.prepare('DELETE FROM chunks WHERE file_path = ?'),
    stmtDeleteFts: db.prepare('DELETE FROM fts_index WHERE file_path = ?'),
    stmtInsertChunk: db.prepare(`
      INSERT INTO chunks (id, file_path, title, content, h1, h2, h3, h4, parent_headers, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `),
    stmtInsertFts: db.prepare(`
      INSERT INTO fts_index (title, content, file_path, chunk_id)
      VALUES (?, ?, ?, ?)
    `),
    stmtSearch: db.prepare(`
      SELECT f.chunk_id as id, f.file_path as filePath, f.title, f.content,
             c.h1, c.h2, c.h3, c.h4, c.parent_headers as parentHeadersJson,
             c.updated_at as updatedAt, rank
      FROM fts_index f
      JOIN chunks c ON f.chunk_id = c.id
      WHERE fts_index MATCH ?
      ORDER BY rank
      LIMIT ?
    `),
    stmtInsertVector: db.prepare(`
      INSERT OR REPLACE INTO chunk_vectors (chunk_id, file_path, vector)
      VALUES (?, ?, ?)
    `),
    stmtDeleteVectors: db.prepare('DELETE FROM chunk_vectors WHERE file_path = ?'),
    stmtGetAllVectors: db.prepare(`
      SELECT cv.chunk_id as chunkId, cv.file_path as filePath, cv.vector as vectorJson,
             c.title, c.content, c.h1, c.h2, c.h3, c.h4, c.parent_headers as parentHeadersJson
      FROM chunk_vectors cv
      JOIN chunks c ON cv.chunk_id = c.id
    `),
    stmtGetChunkById: db.prepare(`
      SELECT id, file_path as filePath, title, content, h1, h2, h3, h4, parent_headers as parentHeadersJson
      FROM chunks
      WHERE id = ?
    `),
  };
}
