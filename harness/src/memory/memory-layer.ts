/**
 * Memory Layer - Codebase memory integration for both personas
 * Interfaces with codebase-memory-mcp for semantic search and graph traversal
 */

import { MemoryConfig, MemoryLayer, CodebaseMemory, ProjectMemory, UserPreferences, Decision } from '../core/types';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

export class MemoryLayerImpl {
  private config: MemoryConfig;
  private configRoot: string;
  private memoryCache: MemoryLayer;
  private codebaseMemoryEnabled: boolean;

  constructor(config: MemoryConfig, configRoot: string) {
    this.config = config;
    this.configRoot = configRoot;
    this.codebaseMemoryEnabled = config.codebaseMemoryEnabled;
    this.memoryCache = this.loadMemory();
  }

  private loadMemory(): MemoryLayer {
    const memoryDir = path.join(this.configRoot, '.claude', 'memory');
    const defaultMemory: MemoryLayer = {
      codebase: { filesList: [], concepts: [], relationships: [], graphIndexed: false, lastIndexed: null, symbols: 0, files: 0 },
      project: { decisions: [], tasks: [], conventions: [], facts: [] },
      user: { preferences: {}, patterns: [], defaultPersona: 'mekong', defaultModel: '', language: 'both', autoCompact: false },
    };

    if (!fs.existsSync(memoryDir)) return defaultMemory;

    try {
      const codebaseFile = path.join(memoryDir, 'codebase.json');
      const projectFile = path.join(memoryDir, 'project.json');
      const userFile = path.join(memoryDir, 'user.json');

      const codebase = fs.existsSync(codebaseFile) ? JSON.parse(fs.readFileSync(codebaseFile, 'utf-8')) : defaultMemory.codebase;
      const project = fs.existsSync(projectFile) ? JSON.parse(fs.readFileSync(projectFile, 'utf-8')) : defaultMemory.project;
      const user = fs.existsSync(userFile) ? JSON.parse(fs.readFileSync(userFile, 'utf-8')) : defaultMemory.user;

      return { codebase, project, user };
    } catch {
      return defaultMemory;
    }
  }

  async saveMemory(): Promise<void> {
    const memoryDir = path.join(this.configRoot, '.claude', 'memory');
    if (!fs.existsSync(memoryDir)) {
      fs.mkdirSync(memoryDir, { recursive: true });
    }

    try {
      fs.writeFileSync(
        path.join(memoryDir, 'codebase.json'),
        JSON.stringify(this.memoryCache.codebase, null, 2)
      );
      fs.writeFileSync(
        path.join(memoryDir, 'project.json'),
        JSON.stringify(this.memoryCache.project, null, 2)
      );
      fs.writeFileSync(
        path.join(memoryDir, 'user.json'),
        JSON.stringify(this.memoryCache.user, null, 2)
      );
    } catch (err) {
      console.error('[MemoryLayer] Failed to save memory:', err);
    }
  }

  // ============================================================
  // CODEBASE MEMORY (via codebase-memory-mcp)
  // ============================================================

  /**
   * Search the codebase graph for symbols matching a pattern
   */
  async searchGraph(pattern: string, options: { limit?: number; label?: string } = {}): Promise<any[]> {
    if (!this.codebaseMemoryEnabled) return [];

    return this.invokeMCP('search_graph', {
      name_pattern: pattern,
      label: options.label,
      limit: options.limit || 20,
    });
  }

  /**
   * Trace a path through the call graph
   */
  async tracePath(functionName: string, mode: 'calls' | 'data_flow' | 'cross_service' = 'calls', options: { maxDepth?: number } = {}): Promise<any[]> {
    if (!this.codebaseMemoryEnabled) return [];

    return this.invokeMCP('trace_path', {
      function_name: functionName,
      mode,
      max_depth: options.maxDepth || 5,
    });
  }

  /**
   * Get exact code snippet for a qualified name
   */
  async getCodeSnippet(qualifiedName: string): Promise<string | null> {
    if (!this.codebaseMemoryEnabled) return null;

    const result = await this.invokeMCP('get_code_snippet', {
      qualified_name: qualifiedName,
    });
    return result?.content || null;
  }

  /**
   * Execute arbitrary Cypher query on the codebase graph
   */
  async queryGraph(query: string): Promise<any[]> {
    if (!this.codebaseMemoryEnabled) return [];

    return this.invokeMCP('query_graph', { query });
  }

  /**
   * Invoke codebase-memory-mcp CLI
   */
  private async invokeMCP(method: string, params: any): Promise<any> {
    const mcpBin = '/Users/macbook/.local/bin/codebase-memory-mcp';
    if (!fs.existsSync(mcpBin)) return [];

    return new Promise((resolve) => {
      const proc = spawn(mcpBin, ['query', method, JSON.stringify(params)], {
        cwd: this.configRoot,
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, CACHE_DIR: path.join(this.configRoot, '.claude', 'codebase-memory') },
      });

      let stdout = '';
      let stderr = '';

      proc.stdout?.on('data', (data) => { stdout += data.toString(); });
      proc.stderr?.on('data', (data) => { stderr += data.toString(); });

      proc.on('close', (code) => {
        try {
          if (stdout.trim()) {
            const result = JSON.parse(stdout);
            resolve(result);
          } else {
            resolve([]);
          }
        } catch {
          resolve([]);
        }
      });

      proc.on('error', () => resolve([]));
    });
  }

  // ============================================================
  // PROJECT MEMORY
  // ============================================================

  addFact(fact: string, source: string = 'user'): void {
    this.memoryCache.project.facts.push({
      fact,
      source,
      timestamp: new Date().toISOString(),
    });
    this.saveMemory();
  }

  addDecision(decision: { question: string; options: string[]; chosen: string; rationale: string }): void {
    this.memoryCache.project.decisions.push({
      id: `dec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      ...decision,
      timestamp: new Date().toISOString(),
    });
    this.saveMemory();
  }

  getFacts(): any[] {
    return this.memoryCache.project.facts;
  }

  getDecisions(): Decision[] {
    return this.memoryCache.project.decisions as Decision[];
  }

  // ============================================================
  // USER PREFERENCES
  // ============================================================

  setUserPreference(key: string, value: any): void {
    this.memoryCache.user.preferences[key] = value;
    this.saveMemory();
  }

  getUserPreference(key: string): any {
    return this.memoryCache.user.preferences[key];
  }

  // ============================================================
  // CACHE ACCESS
  // ============================================================

  getMemory(): MemoryLayer {
    return this.memoryCache;
  }

  getCodebaseMemory(): CodebaseMemory {
    return this.memoryCache.codebase;
  }

  getProjectMemory(): ProjectMemory {
    return this.memoryCache.project;
  }

  getUserPreferences(): UserPreferences {
    return this.memoryCache.user;
  }
}
