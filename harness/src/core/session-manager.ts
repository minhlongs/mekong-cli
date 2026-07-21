/**
 * Session Manager - Handles session state, history, and memory for dual personas
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { SessionState, MemoryLayer, CodebaseMemory, ProjectMemory, UserPreferences, Persona, AgentInvocation, HistoryEntry, Decision, TaskRef, Convention, ProjectFact } from '../core/types';
import { ConfigManager } from './config-manager';

export class SessionManager {
  private sessionDir: string;
  private currentSession: SessionState | null = null;
  private configManager: ConfigManager;
  private maxHistoryTokens: number;

  constructor(configManager: ConfigManager, maxHistoryTokens = 200000) {
    this.configManager = configManager;
    this.maxHistoryTokens = maxHistoryTokens;
    this.sessionDir = path.join(configManager.getConfigRoot(), '.sessions');
    this.ensureSessionDir();
  }

  private ensureSessionDir(): void {
    if (!fs.existsSync(this.sessionDir)) {
      fs.mkdirSync(this.sessionDir, { recursive: true });
    }
  }

  async createSession(persona: Persona, workingDir: string): Promise<SessionState> {
    const sessionId = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    const sessionFile = path.join(this.sessionDir, `${sessionId}.json`);

    const session: SessionState = {
      id: sessionId,
      persona,
      workingDir,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      history: [],
      memory: {
        codebase: { filesList: [], concepts: [], relationships: [], graphIndexed: false, lastIndexed: null, symbols: 0, files: 0 },
        project: { decisions: [], tasks: [], conventions: [], facts: [] },
        user: { preferences: {}, patterns: [], defaultPersona: persona, defaultModel: '', language: 'both', autoCompact: false },
      },
      contextTokens: 0,
      currentPersona: persona,
      agentInvocations: [],
      hookOutputs: {},
      spawnedAgents: [],
    };

    await this.saveSession(session);
    this.currentSession = session;
    return session;
  }

  async loadSession(sessionId: string): Promise<SessionState | null> {
    const sessionFile = path.join(this.sessionDir, `${sessionId}.json`);
    if (!fs.existsSync(sessionFile)) return null;

    try {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf-8'));
      // Convert date strings back to Date objects
      this.currentSession = this.deserializeSession(data);
      return this.currentSession;
    } catch {
      return null;
    }
  }

  async loadLatestSession(persona: Persona): Promise<SessionState | null> {
    if (!fs.existsSync(this.sessionDir)) return null;

    const files = fs.readdirSync(this.sessionDir)
      .filter(f => f.endsWith('.json'))
      .map(f => ({
        name: f,
        time: fs.statSync(path.join(this.sessionDir, f)).mtime.getTime(),
      }))
      .sort((a, b) => b.time - a.time);

    for (const file of files) {
      const session = await this.loadSession(file.name.replace('.json', ''));
      if (session && session.currentPersona === persona) return session;
    }
    return null;
  }

  private deserializeSession(data: any): SessionState {
    return {
      ...data,
      createdAt: data.createdAt,
      updatedAt: data.updatedAt,
      history: data.history.map((h: any) => ({ ...h, timestamp: h.timestamp })),
      memory: {
        ...data.memory,
        codebase: {
          ...data.memory.codebase,
          lastIndexed: data.memory.codebase.lastIndexed || null,
        },
        user: {
          ...data.memory.user,
          defaultPersona: data.memory.user.defaultPersona as Persona,
        },
        project: {
          ...data.memory.project,
          decisions: data.memory.project.decisions.map((d: any) => ({ ...d, timestamp: d.timestamp })),
          facts: data.memory.project.facts.map((f: any) => ({ ...f, timestamp: f.timestamp })),
        },
      },
      agentInvocations: data.agentInvocations.map((a: any) => ({
        ...a,
        startedAt: a.startedAt,
        completedAt: a.completedAt,
      })),
      spawnedAgents: data.spawnedAgents.map((a: any) => ({
        ...a,
        startedAt: a.startedAt,
        completedAt: a.completedAt,
      })),
    };
  }

  async saveSession(session: SessionState): Promise<void> {
    session.updatedAt = new Date().toISOString();
    const sessionFile = path.join(this.sessionDir, `${session.id}.json`);
    fs.writeFileSync(sessionFile, JSON.stringify(session, null, 2));
    this.currentSession = session;
  }

  async switchPersona(sessionId: string, newPersona: Persona): Promise<SessionState | null> {
    const session = await this.loadSession(sessionId);
    if (!session) return null;

    session.currentPersona = newPersona;
    session.persona = newPersona;
    session.agentInvocations = [];

    await this.saveSession(session);
    return session;
  }

  getCurrentSession(): SessionState | null {
    return this.currentSession;
  }

  getCurrentContext(): { sessionId: string; persona: Persona; workingDir: string; history: HistoryEntry[]; memory: MemoryLayer; agentInvocations: AgentInvocation[]; hookOutputs: Record<string, any> } | null {
    if (!this.currentSession) return null;

    return {
      sessionId: this.currentSession.id,
      persona: this.currentSession.currentPersona,
      workingDir: this.currentSession.workingDir,
      history: this.currentSession.history,
      memory: this.currentSession.memory,
      agentInvocations: this.currentSession.agentInvocations,
      hookOutputs: this.currentSession.hookOutputs,
    };
  }

  addToHistory(entry: { role: 'user' | 'assistant' | 'tool' | 'agent'; content: string; tokens?: number }): void {
    if (!this.currentSession) return;

    const tokens = entry.tokens || this.estimateTokens(entry.content);
    this.currentSession.history.push({
      id: `hist_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toISOString(),
      type: entry.role,
      content: entry.content,
      persona: this.currentSession.currentPersona,
      tokens,
    });
    this.currentSession.contextTokens += tokens;

    this.trimHistory();
  }

  private trimHistory(): void {
    if (!this.currentSession) return;

    while (this.currentSession.contextTokens > this.maxHistoryTokens && this.currentSession.history.length > 1) {
      const removed = this.currentSession.history.shift();
      if (removed) {
        this.currentSession.contextTokens -= removed.tokens || 0;
      }
    }
  }

  private estimateTokens(text: string): number {
    return Math.ceil(text.length / 3);
  }

  recordAgentInvocation(invocation: {
    id: string;
    agentType: string;
    prompt: string;
    status: 'running' | 'completed' | 'failed';
    result?: any;
    startedAt: string;
    completedAt?: string;
  }): void {
    if (!this.currentSession) return;
    this.currentSession.agentInvocations.push(invocation);
  }

  updateAgentInvocation(agentId: string, updates: Partial<{
    status: 'running' | 'completed' | 'failed';
    result: any;
    completedAt: string;
  }>): void {
    if (!this.currentSession) return;
    const idx = this.currentSession.agentInvocations.findIndex(i => i.id === agentId);
    if (idx >= 0) {
      this.currentSession.agentInvocations[idx] = {
        ...this.currentSession.agentInvocations[idx],
        ...updates,
      };
    }
  }

  addHookOutput(hookId: string, output: any): void {
    if (!this.currentSession) return;
    this.currentSession.hookOutputs = this.currentSession.hookOutputs || {};
    this.currentSession.hookOutputs[hookId] = output;
  }

  getMemory(): MemoryLayer {
    return this.currentSession?.memory || {
      codebase: { filesList: [], concepts: [], relationships: [], graphIndexed: false, lastIndexed: null, symbols: 0, files: 0 },
      project: { decisions: [], tasks: [], conventions: [], facts: [] },
      user: { preferences: {}, patterns: [], defaultPersona: 'mekong', defaultModel: '', language: 'both', autoCompact: false },
    };
  }

  addFact(fact: string, source: string = 'user'): void {
    if (!this.currentSession) return;
    this.currentSession.memory.project.facts.push({
      fact,
      source,
      timestamp: new Date().toISOString(),
    });
    this.saveSession(this.currentSession);
  }

  addDecision(decision: { question: string; options: string[]; chosen: string; rationale: string }): void {
    if (!this.currentSession) return;
    this.currentSession.memory.project.decisions.push({
      id: `dec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      ...decision,
      timestamp: new Date().toISOString(),
    });
    this.saveSession(this.currentSession);
  }

  getFacts(): ProjectFact[] {
    return this.currentSession?.memory.project.facts || [];
  }

  getDecisions(): Decision[] {
    return this.currentSession?.memory.project.decisions || [];
  }

  setUserPreference(key: string, value: any): void {
    if (!this.currentSession) return;
    this.currentSession.memory.user.preferences[key] = value;
    this.saveSession(this.currentSession);
  }

  getUserPreference(key: string): any {
    return this.currentSession?.memory.user.preferences[key];
  }

  async listSessions(): Promise<Array<{ id: string; persona: Persona; createdAt: string; updatedAt: string }>> {
    if (!fs.existsSync(this.sessionDir)) return [];

    const files = fs.readdirSync(this.sessionDir)
      .filter(f => f.endsWith('.json'))
      .map(f => {
        const filePath = path.join(this.sessionDir, f);
        const stat = fs.statSync(filePath);
        try {
          const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
          return {
            id: data.id,
            persona: data.persona,
            createdAt: data.createdAt,
            updatedAt: data.updatedAt,
          };
        } catch {
          return null;
        }
      })
      .filter(Boolean) as any[];

    return files.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
  }

  async deleteSession(sessionId: string): Promise<boolean> {
    const sessionFile = path.join(this.sessionDir, `${sessionId}.json`);
    if (fs.existsSync(sessionFile)) {
      fs.unlinkSync(sessionFile);
      if (this.currentSession?.id === sessionId) {
        this.currentSession = null;
      }
      return true;
    }
    return false;
  }
}