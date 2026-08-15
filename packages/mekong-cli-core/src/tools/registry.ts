import type { ToolDefinition, ToolResult } from '../types/tool.js';
import { SecurityManager } from './security.js';
import { emit } from '../core/events.js';

export class ToolRegistry {
  private tools: Map<string, ToolDefinition> = new Map();
  private security: SecurityManager;

  constructor(security?: SecurityManager) {
    this.security = security ?? new SecurityManager();
  }

  /** Register a single tool */
  register(tool: ToolDefinition): void {
    this.tools.set(tool.name, tool);
  }

  /** Register multiple tools at once */
  registerAll(tools: ToolDefinition[]): void {
    for (const tool of tools) this.register(tool);
  }

  /** Execute a tool by name with security check */
  async execute(
    name: string,
    params: Record<string, unknown>,
    context?: string,
  ): Promise<ToolResult> {
    const tool = this.tools.get(name);
    if (!tool) {
      return { success: false, output: '', error: `Tool "${name}" not found` };
    }

    const permission = await this.security.checkPermission(
      name,
      tool.securityLevel,
      context ?? name,
    );
    if (!permission.allowed) {
      return { success: false, output: '', error: `Permission denied: ${permission.reason}` };
    }

    emit('tool:called', { name, params });
    const startTime = Date.now();

    try {
      const result = await tool.execute(params);
      const durationMs = Date.now() - startTime;
      emit('tool:result', { name, success: result.success, durationMs });
      return result;
    } catch (error) {
      const err = error instanceof Error ? error.message : String(error);
      emit('tool:result', { name, success: false, error: err });
      return {
        success: false,
        output: '',
        error: err,
        metadata: { durationMs: Date.now() - startTime },
      };
    }
  }

  /** Get a tool definition by name */
  get(name: string): ToolDefinition | undefined {
    return this.tools.get(name);
  }

  /** List all registered tool definitions */
  list(): ToolDefinition[] {
    return Array.from(this.tools.values());
  }

  /** List tool names filtered by category */
  listByCategory(category: ToolDefinition['category']): string[] {
    return this.list()
      .filter((t) => t.category === category)
      .map((t) => t.name);
  }

  /** Check if a tool is registered */
  has(name: string): boolean {
    return this.tools.has(name);
  }

  /** Number of registered tools */
  get size(): number {
    return this.tools.size;
  }
}
