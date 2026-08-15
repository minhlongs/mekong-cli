import { AskDatabase, Chunk } from './db';
import { parseMarkdown } from './parser';
import { AskReranker } from './reranker';

export function getHashingEmbedding(text: string, dimensions = 384): number[] {
  const vector = new Array(dimensions).fill(0);
  const cleanText = text.toLowerCase().replace(/[^a-z0-9\s]/g, '');
  
  for (let i = 0; i < cleanText.length - 2; i++) {
    const trigram = cleanText.substring(i, i + 3);
    let hash = 2166136261;
    for (let j = 0; j < trigram.length; j++) {
      hash ^= trigram.charCodeAt(j);
      hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
    }
    const index = Math.abs(hash) % dimensions;
    vector[index] += 1;
  }
  
  let sumSq = 0;
  for (let v of vector) {
    sumSq += v * v;
  }
  const norm = Math.sqrt(sumSq);
  
  if (norm > 0) {
    for (let i = 0; i < dimensions; i++) {
      vector[i] /= norm;
    }
  } else {
    vector[0] = 1.0;
  }
  
  return vector;
}

export class AskRetriever {
  private db: AskDatabase;
  private reranker: AskReranker;

  constructor(db: AskDatabase) {
    this.db = db;
    this.reranker = new AskReranker();
  }

  /**
   * Generates embedding vector for a given text.
   * Attempts local server first, falls back to feature hashing.
   */
  public async getEmbedding(text: string): Promise<number[]> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    try {
      const serverUrl = process.env.MODEL_SERVER_URL || 'http://localhost:11437';
      const modelName = process.env.MODEL_NAME || 'mlx-community/Qwen3.6-35B-A3B-4bit';
      const token = process.env.MODEL_SERVER_TOKEN || 'mlx';

      const embeddingUrl = serverUrl.includes('/v1/') || serverUrl.endsWith('/v1')
        ? (serverUrl.endsWith('/v1') ? `${serverUrl}/embeddings` : serverUrl)
        : `${serverUrl.replace(/\/$/, '')}/v1/embeddings`;

      const response = await fetch(embeddingUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: modelName,
          input: text
        }),
        signal: controller.signal
      });

      if (response.ok) {
        const data = (await response.json()) as any;
        const embedding = data.data?.[0]?.embedding;
        if (Array.isArray(embedding)) {
          return embedding;
        }
      }
    } catch (e) {
      // Offline fallback
    } finally {
      clearTimeout(timeoutId);
    }

    return getHashingEmbedding(text);
  }

  /**
   * Indexes a markdown file: parses, records chunks, generates embeddings, and indexes them.
   */
  public async indexFile(filePath: string, markdownContent: string): Promise<void> {
    const chunks = parseMarkdown(filePath, markdownContent);
    this.db.indexChunks(filePath, chunks);

    for (const chunk of chunks) {
      const vector = await this.getEmbedding(chunk.content);
      this.db.saveVector(chunk.id, filePath, vector);
    }
  }

  /**
   * Performs hybrid search (BM25 + Dense) merged with RRF and reranked.
   */
  public async retrieve(query: string, limit: number = 5): Promise<Chunk[]> {
    if (!query.trim()) {
      return [];
    }

    // 1. Sparse Match List (FTS5 BM25)
    const ftsResults = this.db.search(query, limit * 3);

    // 2. Dense Match List (Vector Cosine Similarity)
    const queryVector = await this.getEmbedding(query);
    const storedVectors = this.db.getAllVectors();

    const denseResultsWithScore = storedVectors.map(sv => {
      const score = cosineSimilarity(queryVector, sv.vector);
      return { chunk: sv.chunk, score };
    });

    // Sort dense results by similarity descending
    const denseResults = denseResultsWithScore
      .sort((a, b) => b.score - a.score)
      .map(item => item.chunk);

    // 3. Reciprocal Rank Fusion (RRF)
    const k = 60;
    const rrfScores = new Map<string, { chunk: Chunk; score: number }>();

    // Map chunk ID to rank in FTS
    ftsResults.forEach((c, index) => {
      const rank = index + 1;
      const current = rrfScores.get(c.id) || { chunk: c, score: 0 };
      current.score += 1.0 / (k + rank);
      rrfScores.set(c.id, current);
    });

    // Map chunk ID to rank in Dense
    denseResults.forEach((c, index) => {
      const rank = index + 1;
      const current = rrfScores.get(c.id) || { chunk: c, score: 0 };
      current.score += 1.0 / (k + rank);
      rrfScores.set(c.id, current);
    });

    // Sort candidates by RRF score descending
    const candidates = Array.from(rrfScores.values())
      .sort((a, b) => b.score - a.score)
      .map(item => item.chunk);

    // Take top candidates for reranking
    const topCandidates = candidates.slice(0, limit * 3);

    // 4. Reranking
    const reranked = this.reranker.rerank(query, topCandidates);

    // Return the top limit chunks
    return reranked.slice(0, limit).map(item => item.chunk);
  }
}

function cosineSimilarity(v1: number[], v2: number[]): number {
  if (v1.length !== v2.length || v1.length === 0) {
    return 0;
  }
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < v1.length; i++) {
    dotProduct += v1[i] * v2[i];
    normA += v1[i] * v1[i];
    normB += v2[i] * v2[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}
