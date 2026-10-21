import { Database } from 'bun:sqlite';
import { dirname } from 'path';
import { mkdirSync, existsSync } from 'fs';
import {
  type Chunk,
  type SearchResult,
  type PreparedStatements,
  DEFAULT_DB_DIR,
  DEFAULT_DB_PATH,
  initDatabaseSchema,
  prepareDatabaseStatements,
} from './db-schema';
import { mapAllVectors, mapChunkById, searchFts } from './db-queries';

export type { Chunk, SearchResult };
export { DEFAULT_DB_DIR, DEFAULT_DB_PATH };

export class AskDatabase {
  private db: Database;
  private dbPath: string;
  private stmts!: PreparedStatements;

  constructor(dbPath: string = DEFAULT_DB_PATH) {
    this.dbPath = dbPath;
    const dir = dirname(dbPath);
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
    this.db = new Database(dbPath);
    this.db.exec('PRAGMA journal_mode = WAL;');
    this.init();
    this.stmts = prepareDatabaseStatements(this.db);
  }

  /**
   * Initializes the SQLite schema and FTS5 virtual table.
   */
  public init(): void {
    initDatabaseSchema(this.db);
  }

  /**
   * Cleans up all indexed chunks and search indexes for a specific file.
   */
  public deleteFile(filePath: string): void {
    const transaction = this.db.transaction(() => {
      this.stmts.stmtDeleteChunks.run(filePath);
      this.stmts.stmtDeleteFts.run(filePath);
      this.stmts.stmtDeleteVectors.run(filePath);
    });

    transaction();
  }

  /**
   * Indexes a list of chunks for a file. Old chunks for the same file are deleted first.
   */
  public indexChunks(filePath: string, chunks: Chunk[]): void {
    const updatedAt = new Date().toISOString();

    const transaction = this.db.transaction(() => {
      this.stmts.stmtDeleteChunks.run(filePath);
      this.stmts.stmtDeleteFts.run(filePath);
      this.stmts.stmtDeleteVectors.run(filePath);

      for (const chunk of chunks) {
        this.stmts.stmtInsertChunk.run(
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

        this.stmts.stmtInsertFts.run(
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
    this.stmts.stmtInsertVector.run(chunkId, filePath, JSON.stringify(vector));
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
    return mapAllVectors(this.stmts.stmtGetAllVectors);
  }

  /**
   * Gets a specific chunk by its ID.
   */
  public getChunkById(id: string): Chunk | null {
    return mapChunkById(this.stmts.stmtGetChunkById, id);
  }

  /**
   * Performs full-text search against the index.
   */
  public search(query: string, limit: number = 10): SearchResult[] {
    return searchFts(this.stmts.stmtSearch, query, limit);
  }

  /**
   * Closes the database connection.
   */
  public close(): void {
    this.db.close();
  }
}
