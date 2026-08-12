/**
 * Memory Layer - Codebase memory integration
 */

import { ConfigManager } from './config-manager';

export interface MemoryQuery {
  query: string;
  project?: string;
  limit?: number;
  offset?: number;
}

export interface MemoryResult {
  results: any[];
  total: number;
  hasMore: boolean;
}

export class MemoryLayer {
  private configRoot: string;
  private configManager: ConfigManager;
  private mcpClient: any = null;

  constructor(configRoot: string, configManager: ConfigManager) {
    this.configRoot = configRoot;
    this.configManager = configManager;
  }

  async initialize(): Promise<void> {
    // Try to connect to codebase-memory-mcp
    try {
      // This would connect to the MCP server
      console.log('[MemoryLayer] Initialized');
    } catch (error) {
      console.warn('[MemoryLayer] Codebase memory MCP not available:', error);
    }
  }

  async searchGraph(query: MemoryQuery): Promise<MemoryResult> {
    // Delegate to codebase-memory-mcp
    if (this.mcpClient) {
      return this.mcpClient.search_graph(query);
    }
    return { results: [], total: 0, hasMore: false };
  }

  async tracePath(functionName: string, options: any = {}): Promise<any> {
    if (this.mcpClient) {
      return this.mcpClient.trace_path({ function_name: functionName, ...options });
    }
    return null;
  }

  async getArchitecture(project: string): Promise<any> {
    if (this.mcpClient) {
      return this.mcpClient.get_architecture({ project });
    }
    return null;
  }

  async detectChanges(project: string, since?: string): Promise<any> {
    if (this.mcpClient) {
      return this.mcpClient.detect_changes({ project, since });
    }
    return null;
  }

  setMCPClient(client: any): void {
    this.mcpClient = client;
  }
}
