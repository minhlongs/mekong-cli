import type { ToolDefinition, ToolResult } from '../../types/tool.js';

export function createHttpTool(): ToolDefinition {
  return {
    name: 'http',
    description: 'Make HTTP requests (GET/POST/PUT/DELETE)',
    category: 'network',
    securityLevel: 2,
    params: [
      { name: 'url', type: 'string', description: 'Request URL', required: true },
      { name: 'method', type: 'string', description: 'HTTP method (default: GET)', required: false },
      { name: 'body', type: 'string', description: 'Request body (JSON string)', required: false },
      { name: 'headers', type: 'object', description: 'Additional request headers', required: false },
    ],
    execute: async (params): Promise<ToolResult> => {
      const startTime = Date.now();
      try {
        const response = await fetch(params.url as string, {
          method: (params.method as string) ?? 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...((params.headers as Record<string, string>) ?? {}),
          },
          body: params.body ? String(params.body) : undefined,
          signal: AbortSignal.timeout(30000),
        });
        const text = await response.text();
        return {
          success: response.ok,
          output: text,
          metadata: {
            status: response.status,
            headers: Object.fromEntries(response.headers),
            durationMs: Date.now() - startTime,
          },
        };
      } catch (error) {
        return {
          success: false,
          output: '',
          error: String(error),
          metadata: { durationMs: Date.now() - startTime },
        };
      }
    },
  };
}
