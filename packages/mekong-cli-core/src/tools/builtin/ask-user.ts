import type { ToolDefinition, ToolResult } from '../../types/tool.js';

const defaultAsk = async (q: string): Promise<string> => {
  console.log(`[ASK] ${q}`);
  return '(no interactive input available)';
};

/** Creates a human-in-the-loop tool. askFn is injected by the CLI layer. */
export function createAskUserTool(askFn?: (question: string) => Promise<string>): ToolDefinition {
  return {
    name: 'ask_user',
    description: 'Ask the user a question and wait for their response',
    category: 'custom',
    securityLevel: 0,
    params: [
      { name: 'question', type: 'string', description: 'Question to ask the user', required: true },
    ],
    execute: async (params): Promise<ToolResult> => {
      const fn = askFn ?? defaultAsk;
      const answer = await fn(params.question as string);
      return { success: true, output: answer };
    },
  };
}
