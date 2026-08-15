import { expect, test, describe, beforeAll, afterAll } from "bun:test";
import { AskDatabase } from "../src/db.js";
import { AskRetriever } from "../src/retriever.js";
import { join } from "path";
import { tmpdir } from "os";
import { unlinkSync, existsSync } from "fs";

describe("Ask CLI Integration & Verification Tests", () => {
  let dbPath: string;
  let db: AskDatabase;
  let retriever: AskRetriever;

  beforeAll(() => {
    dbPath = join(tmpdir(), `ask-integration-test-${Date.now()}.db`);
    db = new AskDatabase(dbPath);
    retriever = new AskRetriever(db);
  });

  afterAll(() => {
    db.close();
    if (existsSync(dbPath)) {
      unlinkSync(dbPath);
    }
  });

  test("should correctly index rules and return structured context", async () => {
    // 1. Seed mock rules
    const ruleContent = `
# Primary Workflow

## Unit Testing

All unit tests must pass before code changes can be merged. No mock data is allowed in production verification.
    `.trim();

    await retriever.indexFile(".claude/rules/primary-workflow.md", ruleContent);

    // 2. Query matching semantic intent "rules for tests"
    const results = await retriever.retrieve("rules for tests", 3);
    
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toBe("Unit Testing");
    expect(results[0].parentHeaders).toEqual(["Primary Workflow"]);
    expect(results[0].content).toContain("All unit tests must pass");
  });

  test("should prioritize rule directory matches when querying for system constraints", async () => {
    // Index a doc file with similar keywords to see if rules are prioritized
    const docContent = `
# General Documentation

## Testing Guidelines

Some random guidelines about writing code and running QA scripts on staging.
    `.trim();

    await retriever.indexFile("docs/testing.md", docContent);

    // Retrieve querying system constraint word "workflow"
    const results = await retriever.retrieve("workflow testing constraints", 2);
    expect(results.length).toBeGreaterThan(0);
    
    // The top matched chunk should be from .claude/rules/ due to the rule boost in reranker!
    expect(results[0].filePath).toContain(".claude/rules/");
  });
});
