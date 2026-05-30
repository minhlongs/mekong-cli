# Subsystem Audit: packages/ask-core

## 1. Purpose
- **Business Role**: Serves as the search and retrieval core for mekong-cli tools/workspace. It allows ingestion, semantic categorization, indexing, and querying of developer guidelines, rules, and documentation.
- **Technical Role**: A private TypeScript module (`@mekong/ask-core`) executing on Bun. It implements Markdown document parsing, FTS5 virtual tables (SQLite) for BM25 keyword matching, vector embeddings generation (remote LLM or trigram-based feature-hashing local fallback), cosine similarity calculations, reciprocal rank fusion (RRF), and custom heuristic scoring rerank.

## 2. Entry Points
- **Module Exports**: `src/index.ts` is the public API entry point. It exports classes `AskDatabase`, `AskRetriever`, `AskReranker`, functions like `parseMarkdown`, `generateChunkId`, and types (`Chunk`, `SearchResult`).
- **Tests**: Located in `tests/*.ts` (e.g., `ask.test.ts`, `db.test.ts`, `parser.test.ts`, `retriever.test.ts`), executing via Bun's native test runner (`bun test`).

## 3. Runtime Lifecycle
- **Initialization (`AskDatabase.constructor` at `src/db.ts:39`)**:
  1. Resolves database path (defaults to `~/.mekong/ask/ask.db`).
  2. Ensures the target directory exists (`fs.mkdirSync`).
  3. Opens database connection using `bun:sqlite`'s `Database`.
  4. Enables WAL mode (`PRAGMA journal_mode = WAL;`) for concurrent execution.
  5. Initializes schema: tables `chunks`, `chunk_vectors`, and FTS5 virtual table `fts_index`.
  6. Compiles/pre-compiles SQL prepared statements to optimize latency (`prepareStatements()`).
- **Indexing Flow (`AskRetriever.indexFile` at `src/retriever.ts:95`)**:
  1. Splitting: Parses raw markdown content with `parseMarkdown()`, stripping frontmatter, splitting content into sections at headers `#` through `####`, and ignoring code block boundaries.
  2. Chunk ID: Computes deterministic chunk hashes via SHA-256 (`generateChunkId()`).
  3. Database Transaction: Within a SQLite transaction, deletes old records for the same file from tables (`chunks`, `fts_index`, `chunk_vectors`) and inserts the new parsed chunks.
  4. Vector Generation: For each chunk, generates a dense embedding vector using `getEmbedding()`.
  5. Vector Persistence: Saves JSON-serialized vector arrays into the `chunk_vectors` table.
- **Query Flow (`AskRetriever.retrieve` at `src/retriever.ts:108`)**:
  1. Sanitizes query syntax to avoid FTS errors (`sanitizeFtsQuery()` wraps terms containing `-`, `:`, `/`, `\` in double quotes).
  2. Runs sparse FTS matching on `fts_index` matching query using BM25 rank order.
  3. Generates query vector embedding, reads all vectors from database (`db.getAllVectors()`), calculates cosine similarity in JS memory, and sorts dense results descending.
  4. Reciprocal Rank Fusion (RRF) combines sparse and dense rankings: $Score(c) = \sum \frac{1}{60 + Rank_i(c)}$.
  5. Passes top candidates (`limit * 3`) to the reranker (`AskReranker.rerank()`).
  6. Reranker scores candidates using token matching heuristics (boosting rule directories, title matches, header keywords, content density).
  7. Slices top `limit` results and returns them.

## 4. State Management
- **Persistence**: Managed through SQLite on-disk database files (`~/.mekong/ask/ask.db`).
- **Access Pattern**: Handled synchronously by `bun:sqlite`. Writes (clearing and updating files) are executed within database transactions (`db.transaction()`) to maintain ACID properties.

## 5. Dependencies
- **Internal**: None.
- **External**: `zod` (`^3.24.0` in `package.json` dependencies, but never imported/used in the codebase), `bun-types` and `typescript` (dev dependencies).
- **Platform APIs**: Bun-specific APIs (`bun:sqlite`, `bun:test`) and Node.js standard modules (`crypto`, `path`, `os`, `fs`).

## 6. Failure Modes
- **Model Server Outages**: If the remote model server is offline, embedding HTTP requests fail.
- **Unconstrained Chunk Size**: Large documents lacking headers produce huge chunks, causing downstream token length overflows.
- **Concurrency Write Conflicts**: Under massive indexing loads, SQLite write locks can cause timeouts despite WAL mode.
- **Database Leaks**: Failure to close database instances if instantiated repeatedly.
- **FTS Syntax Invalidation**: Queries with unbalanced quotes or special characters could fail FTS search (returning empty results).

## 7. Recovery Behavior
- **Timeout & Offline Fallback (`src/retriever.ts:50`)**: Uses a `timeout` (2000ms) with `AbortController` when fetching embeddings from `MODEL_SERVER_URL` (defaulting to `http://localhost:11437`). On HTTP errors or aborts, it automatically falls back to trigram-based feature-hashing (`getHashingEmbedding()`).
- **Database Warnings Handling**: FTS Match failures catch and log errors (`console.error`) rather than throwing/crashing. JSON deserialization errors for headers/vectors default to empty arrays.

## 8. Scale Limits
- **In-Memory Cosine Similarity (`src/retriever.ts:117-128`)**: Cosine similarity is computed synchronously in JavaScript memory after pulling *all* vector records using `db.getAllVectors()`. This scales at $O(N)$ memory and CPU where $N$ is the total number of chunks. Under a 10x indexing load, this loop blocks the single-threaded JS runtime, leading to severe query latencies.
- **SQLite Write Locking**: Writes block one another; concurrent file indexing is queued.

## 9. Security Surface
- **Raw SQL Parameters**: Parameterized statements (`MATCH ?`, `id = ?`) are used, mitigating SQL injection.
- **Data Access**: All indexed content is written in plain text in `ask.db`, readable by any user with directory access.
- **HTTP Communications**: Relies on `MODEL_SERVER_TOKEN` (default: `mlx`) passed as `Authorization: Bearer <token>` over HTTP to communicate with the model server.

## 10. Observability
- **Gaps**: Lacks metrics, distributed tracing hooks, or unified logging. Errors are directly logged to `console.error` (e.g. `FTS search failed`).

## 11. Technical Debt
- **Unused Dependency**: `zod` is declared in `package.json` but never imported or utilized.
- **Lack of Chunk Constraints**: No token/character limit splits are implemented during markdown parsing.
- **Vietnam-Specific Rules in Generic Reranker (`src/reranker.ts:61-68`)**: Heuristic boosts for terms like `quy định` and `quy trinh` are hardcoded in the reranker.
- **No Native Vector Index**: Uses manual memory similarity loops instead of SQLite extensions like `sqlite-vec`.

## 12. Missing Knowledge
- Evaluated hash collision rates for the trigram feature-hashing implementation are undocumented.
- The rationale for including `zod` remains unclear.
