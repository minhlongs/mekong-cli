import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { glob } from 'glob';
import type { ToolDefinition, ToolResult } from '../../types/tool.js';

export function createFileReadTool(): ToolDefinition {
  return {
    name: 'file_read',
    description: 'Read the contents of a file',
    category: 'filesystem',
    securityLevel: 0,
    params: [
      { name: 'path', type: 'string', description: 'File path to read', required: true },
    ],
    execute: async (params): Promise<ToolResult> => {
      try {
        const content = await readFile(resolve(params.path as string), 'utf-8');
        return { success: true, output: content };
      } catch (error) {
        return { success: false, output: '', error: String(error) };
      }
    },
  };
}

export function createFileWriteTool(): ToolDefinition {
  return {
    name: 'file_write',
    description: 'Write content to a file, creating parent directories as needed',
    category: 'filesystem',
    securityLevel: 1,
    params: [
      { name: 'path', type: 'string', description: 'File path to write', required: true },
      { name: 'content', type: 'string', description: 'Content to write', required: true },
    ],
    execute: async (params): Promise<ToolResult> => {
      try {
        const filePath = resolve(params.path as string);
        await mkdir(dirname(filePath), { recursive: true });
        await writeFile(filePath, params.content as string, 'utf-8');
        return { success: true, output: `Written to ${filePath}`, metadata: { path: filePath } };
      } catch (error) {
        return { success: false, output: '', error: String(error) };
      }
    },
  };
}

export function createFileSearchTool(): ToolDefinition {
  return {
    name: 'file_search',
    description: 'Search for files using glob patterns',
    category: 'filesystem',
    securityLevel: 0,
    params: [
      { name: 'pattern', type: 'string', description: 'Glob pattern to match files', required: true },
      { name: 'cwd', type: 'string', description: 'Working directory for the search', required: false },
    ],
    execute: async (params): Promise<ToolResult> => {
      try {
        const files = await glob(params.pattern as string, {
          cwd: (params.cwd as string) ?? '.',
        });
        return {
          success: true,
          output: files.join('\n'),
          metadata: { count: files.length },
        };
      } catch (error) {
        return { success: false, output: '', error: String(error) };
      }
    },
  };
}
