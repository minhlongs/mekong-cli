export interface PackageInfo {
  name: string;
  version: string;
  path: string;
  private?: boolean;
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
  peerDependencies?: Record<string, string>;
  workspaces?: string[];
}

export interface DependencyGraph {
  nodes: Record<string, PackageInfo>;
  edges: Array<{ from: string; to: string; type: 'prod' | 'dev' | 'peer' }>;
}

export interface HealthStatus {
  service: string;
  status: 'healthy' | 'degraded' | 'down';
  timestamp: number;
  details?: Record<string, any>;
}

export interface MissionResult {
  id: string;
  timestamp: number;
  goal: string;
  success: boolean;
  durationMs: number;
  error?: string;
  modelUsed?: string;
  tokensUsed?: number;
}
