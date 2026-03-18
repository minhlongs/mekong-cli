/** REST API handlers for AgencyOS dashboard — framework-agnostic, pure functions. */

export interface ApiResponse {
  status: number;
  body: object;
  contentType: string;
}

export interface SystemStatus {
  uptime: number;
  version: string;
  paneCount: number;
  taskCount: number;
}

export interface PaneMetric {
  id: string;
  provider: string;
  state: "idle" | "running" | "error" | "offline";
  project: string;
}

export interface RaasMetrics {
  tenants: number;
  revenue: number;
  health: "healthy" | "degraded" | "down";
}

export interface AgiScore {
  score: number;
  capabilities: string[];
  capabilitiesCount: number;
  evolvedAt: string;
}

type RouteHandler = () => ApiResponse;

const JSON_CT = "application/json";

function ok(body: object): ApiResponse {
  return { status: 200, body, contentType: JSON_CT };
}

function notFound(path: string): ApiResponse {
  return { status: 404, body: { error: `Route not found: ${path}` }, contentType: JSON_CT };
}

function methodNotAllowed(method: string): ApiResponse {
  return { status: 405, body: { error: `Method not allowed: ${method}` }, contentType: JSON_CT };
}

/** AgencyOS Dashboard REST API handler. Routes GET requests to resource handlers. */
export class DashboardApi {
  private startTime: number;
  private version: string;

  constructor(version = "0.1.0") {
    this.startTime = Date.now();
    this.version = version;
  }

  /** Route an incoming request. Only GET is supported for read-only dashboard. */
  handleRequest(method: string, path: string): ApiResponse {
    if (method.toUpperCase() !== "GET") {
      return methodNotAllowed(method);
    }

    const routes: Record<string, RouteHandler> = {
      "/status": () => this.getStatus(),
      "/panes": () => this.getPanes(),
      "/tasks": () => this.getTasks(),
      "/raas": () => this.getRaas(),
      "/agi-score": () => this.getAgiScore(),
    };

    const handler = routes[path];
    return handler ? handler() : notFound(path);
  }

  private getStatus(): ApiResponse {
    const status: SystemStatus = {
      uptime: Math.floor((Date.now() - this.startTime) / 1000),
      version: this.version,
      paneCount: 4,
      taskCount: 0,
    };
    return ok(status);
  }

  private getPanes(): ApiResponse {
    const panes: PaneMetric[] = [
      { id: "pane-0", provider: "claude", state: "running", project: "mekong-cli" },
      { id: "pane-1", provider: "gemini", state: "idle", project: "agencyos" },
      { id: "pane-2", provider: "openai", state: "idle", project: "raas-gateway" },
      { id: "pane-3", provider: "claude", state: "offline", project: "unassigned" },
    ];
    return ok({ panes });
  }

  private getTasks(): ApiResponse {
    return ok({ queued: [], active: [], completed: [] });
  }

  private getRaas(): ApiResponse {
    const metrics: RaasMetrics = { tenants: 0, revenue: 0, health: "healthy" };
    return ok(metrics);
  }

  private getAgiScore(): ApiResponse {
    const score: AgiScore = {
      score: 42,
      capabilities: ["planning", "execution", "verification", "self-reflection"],
      capabilitiesCount: 4,
      evolvedAt: new Date().toISOString(),
    };
    return ok(score);
  }

  /** Register a WebSocket message handler stub (framework supplies the WS connection). */
  registerWebSocketHandler(onMessage: (msg: string) => void): void {
    // Stub — caller wires actual WS transport and calls onMessage on each frame.
    void onMessage;
  }
}
