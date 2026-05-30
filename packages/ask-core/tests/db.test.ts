import { expect, test, describe, beforeAll, afterAll } from "bun:test";
import { AskDatabase, Chunk } from "../src/db.js";
import { join } from "path";
import { tmpdir } from "os";
import { unlinkSync, existsSync } from "fs";

describe("AskDatabase SQLite & FTS5 Indexer", () => {
  let dbPath: string;
  let db: AskDatabase;

  beforeAll(() => {
    dbPath = join(tmpdir(), `ask-test-${Date.now()}.db`);
    db = new AskDatabase(dbPath);
  });

  afterAll(() => {
    db.close();
    if (existsSync(dbPath)) {
      unlinkSync(dbPath);
    }
  });

  test("should initialize schema and virtual tables", () => {
    // Schema should create ask.db and configure WAL
    expect(existsSync(dbPath)).toBe(true);
  });

  test("should index, search, and update chunks in FTS5 database", () => {
    const filePath = "docs/guide.md";
    const chunks: Chunk[] = [
      {
        id: "chunk-1",
        filePath,
        title: "Introduction",
        content: "# Introduction\nWelcome to Mekong CLI guidelines.",
        h1: "Introduction",
        h2: null,
        h3: null,
        h4: null,
        parentHeaders: []
      },
      {
        id: "chunk-2",
        filePath,
        title: "Installation",
        content: "## Installation\nRun pnpm install under the mekong directory.",
        h1: "Introduction",
        h2: "Installation",
        h3: null,
        h4: null,
        parentHeaders: ["Introduction"]
      }
    ];

    // Index chunks
    db.indexChunks(filePath, chunks);

    // Search for term in first chunk
    const results1 = db.search("Welcome");
    expect(results1.length).toBe(1);
    expect(results1[0].id).toBe("chunk-1");
    expect(results1[0].title).toBe("Introduction");
    expect(results1[0].filePath).toBe(filePath);
    expect(results1[0].parentHeaders).toEqual([]);

    // Search for term in second chunk
    const results2 = db.search("pnpm install");
    expect(results2.length).toBe(1);
    expect(results2[0].id).toBe("chunk-2");
    expect(results2[0].title).toBe("Installation");
    expect(results2[0].parentHeaders).toEqual(["Introduction"]);

    // Update index with modified chunks (chunk-2 is updated, chunk-1 is deleted in the file)
    const updatedChunks: Chunk[] = [
      {
        id: "chunk-2-new",
        filePath,
        title: "Installation Setup",
        content: "## Installation Setup\nUse pnpm install --frozen-lockfile now.",
        h1: "Introduction",
        h2: "Installation Setup",
        h3: null,
        h4: null,
        parentHeaders: ["Introduction"]
      }
    ];

    db.indexChunks(filePath, updatedChunks);

    // Old chunk-1 shouldn't be found
    const searchOld = db.search("Welcome");
    expect(searchOld.length).toBe(0);

    // Old chunk-2 shouldn't be found
    const searchOld2 = db.search("under the mekong directory");
    expect(searchOld2.length).toBe(0);

    // New chunk should be found
    const searchNew = db.search("frozen-lockfile");
    expect(searchNew.length).toBe(1);
    expect(searchNew[0].id).toBe("chunk-2-new");
    expect(searchNew[0].title).toBe("Installation Setup");
  });

  test("should handle deleteFile correctly", () => {
    const filePath = "docs/delete-me.md";
    const chunks: Chunk[] = [
      {
        id: "delete-chunk",
        filePath,
        title: "Delete Me",
        content: "This content will be deleted soon.",
        h1: "Delete Me",
        h2: null,
        h3: null,
        h4: null,
        parentHeaders: []
      }
    ];

    db.indexChunks(filePath, chunks);

    // Verify it is there
    expect(db.search("soon").length).toBe(1);

    // Delete file index
    db.deleteFile(filePath);

    // Verify it is gone
    expect(db.search("soon").length).toBe(0);
  });
});
