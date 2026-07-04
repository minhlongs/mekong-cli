import { Chunk } from './db';

export interface RerankResult {
  chunk: Chunk;
  score: number;
}

export class AskReranker {
  /**
   * Reranks candidate chunks based on exact/semantic relevance to the query.
   */
  public rerank(query: string, chunks: Chunk[]): RerankResult[] {
    const cleanQuery = query.toLowerCase().trim();
    if (!cleanQuery) {
      return chunks.map(chunk => ({ chunk, score: 0 }));
    }

    const queryTokens = cleanQuery.split(/\s+/).filter(t => t.length > 1);

    const results: RerankResult[] = chunks.map(chunk => {
      let score = 0.0;
      const title = chunk.title.toLowerCase();
      const content = chunk.content.toLowerCase();

      // 1. Exact matches in title
      if (title.includes(cleanQuery)) {
        score += 2.5;
      }

      // 2. Token overlap in title and headers
      for (const token of queryTokens) {
        if (title.includes(token)) score += 0.6;
        if (chunk.h1 && chunk.h1.toLowerCase().includes(token)) score += 0.4;
        if (chunk.h2 && chunk.h2.toLowerCase().includes(token)) score += 0.4;
        if (chunk.h3 && chunk.h3.toLowerCase().includes(token)) score += 0.4;
        if (chunk.h4 && chunk.h4.toLowerCase().includes(token)) score += 0.4;
      }

      // 3. Keyword density in content
      let contentMatchCount = 0;
      for (const token of queryTokens) {
        if (content.includes(token)) {
          contentMatchCount++;
          // Add score based on occurrence count
          const escapedToken = token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          const regex = new RegExp(escapedToken, 'g');
          const matches = content.match(regex);
          if (matches) {
            score += Math.min(matches.length * 0.05, 0.5); // cap frequency boost
          }
        }
      }
      
      // Token coverage ratio boost
      if (queryTokens.length > 0) {
        const ratio = contentMatchCount / queryTokens.length;
        score += ratio * 1.5;
      }

      // 4. Boost chunks from rules directory if user query contains rules/guidelines keywords
      const isRuleQuery = cleanQuery.includes('rule') || 
                          cleanQuery.includes('quy định') || 
                          cleanQuery.includes('quy trinh') || 
                          cleanQuery.includes('workflow') || 
                          cleanQuery.includes('guideline');
      if (isRuleQuery && chunk.filePath.includes('.claude/rules/')) {
        score += 1.5;
      }

      return {
        chunk,
        score
      };
    });

    // Sort descending by score
    return results.sort((a, b) => b.score - a.score);
  }
}
