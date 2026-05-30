import { expect, test, describe, beforeAll, afterAll } from "bun:test";
import { AskDatabase } from "../src/db.js";
import { AskRetriever } from "../src/retriever.js";
import { join } from "path";
import { tmpdir } from "os";
import { unlinkSync, existsSync } from "fs";

describe("AskRetriever & Reranker Pipeline", () => {
  let dbPath: string;
  let db: AskDatabase;
  let retriever: AskRetriever;

  beforeAll(() => {
    dbPath = join(tmpdir(), `ask-retriever-test-${Date.now()}.db`);
    db = new AskDatabase(dbPath);
    retriever = new AskRetriever(db);
  });

  afterAll(() => {
    db.close();
    if (existsSync(dbPath)) {
      unlinkSync(dbPath);
    }
  });

  test("should index a file and perform semantic + keyword hybrid search", async () => {
    const md = `
# Deployments

Guidelines on deployment architecture.

## Vercel Hosting

We host our frontends on Vercel. Use the cli tool to trigger preview deploys.

## Docker Containers

We pack our backend into Docker containers for Railway and AWS ECS. Use pnpm run build before.
    `.trim();

    await retriever.indexFile("docs/deploy.md", md);

    // Verify it saved chunks
    const vectors = db.getAllVectors();
    expect(vectors.length).toBe(3);

    // Retrieve conceptual query "where are apps hosted?" (semantic match on Vercel / ECS)
    const results = await retriever.retrieve("where are apps hosted", 2);
    expect(results.length).toBeGreaterThan(0);
    
    // The top results should contain either Vercel Hosting or Docker Containers or Deployments
    const titles = results.map(r => r.title);
    expect(titles.some(t => t === "Vercel Hosting" || t === "Docker Containers" || t === "Deployments")).toBe(true);

    // Search query for exact rule keyword "containers"
    const keywordResults = await retriever.retrieve("containers", 1);
    expect(keywordResults.length).toBe(1);
    expect(keywordResults[0].title).toBe("Docker Containers");
  });

  test("should use env variables for embedding URL, model, and token when fetching", async () => {
    const originalUrl = process.env.MODEL_SERVER_URL;
    const originalName = process.env.MODEL_NAME;
    const originalToken = process.env.MODEL_SERVER_TOKEN;
    const originalFetch = globalThis.fetch;

    process.env.MODEL_SERVER_URL = "http://my-custom-model-server:5000/v1";
    process.env.MODEL_NAME = "my-custom-model";
    process.env.MODEL_SERVER_TOKEN = "my-custom-token";

    let fetchedUrl = "";
    let fetchedOptions: any = null;

    globalThis.fetch = (async (url: any, options: any) => {
      fetchedUrl = String(url);
      fetchedOptions = options;
      return new Response(JSON.stringify({
        data: [{ embedding: [0.1, 0.2, 0.3] }]
      }), { status: 200 });
    }) as any;

    try {
      const embedding = await retriever.getEmbedding("test text");
      expect(embedding).toEqual([0.1, 0.2, 0.3]);
      expect(fetchedUrl).toBe("http://my-custom-model-server:5000/v1/embeddings");
      
      const body = JSON.parse(fetchedOptions.body);
      expect(body.model).toBe("my-custom-model");
      expect(body.input).toBe("test text");
      expect(fetchedOptions.headers["Authorization"]).toBe("Bearer my-custom-token");
    } finally {
      if (originalUrl !== undefined) process.env.MODEL_SERVER_URL = originalUrl;
      else delete process.env.MODEL_SERVER_URL;
      
      if (originalName !== undefined) process.env.MODEL_NAME = originalName;
      else delete process.env.MODEL_NAME;

      if (originalToken !== undefined) process.env.MODEL_SERVER_TOKEN = originalToken;
      else delete process.env.MODEL_SERVER_TOKEN;

      globalThis.fetch = originalFetch;
    }
  });
});
