/** Terminal dashboard renderer — pure string output with ANSI colors and box-drawing chars. */

// ANSI escape helpers
const A = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
  cyan: "\x1b[36m",
  blue: "\x1b[34m",
  white: "\x1b[37m",
  bgBlue: "\x1b[44m",
} as const;

function c(color: string, text: string): string {
  return `${color}${text}${A.reset}`;
}

export interface PaneInfo {
  id: string;
  provider: string;
  state: "idle" | "running" | "error" | "offline";
  project: string;
}

export interface TaskEntry {
  id: string;
  name: string;
  status: "queued" | "active" | "completed" | "failed";
  assignedPane: string;
}

export interface DashboardData {
  status: { uptime: number; version: string; paneCount: number; taskCount: number };
  panes: PaneInfo[];
  tasks: TaskEntry[];
  raas: { tenants: number; revenue: number; health: string };
  agiScore: { score: number; capabilitiesCount: number };
}

const STATE_ICON: Record<string, string> = {
  running: c(A.green, "●"),
  idle: c(A.dim, "○"),
  error: c(A.red, "✗"),
  offline: c(A.dim, "—"),
};

const TASK_ICON: Record<string, string> = {
  queued: c(A.yellow, "⏳"),
  active: c(A.green, "▶"),
  completed: c(A.green, "✓"),
  failed: c(A.red, "✗"),
};

function box(title: string, lines: string[], width = 60): string {
  const top = `┌─ ${c(A.bold, title)} ${"─".repeat(Math.max(0, width - title.length - 4))}┐`;
  const bottom = `└${"─".repeat(width - 2)}┘`;
  const body = lines.map((l) => `│ ${l.padEnd(width - 4)} │`);
  return [top, ...body, bottom].join("\n");
}

/** AgencyOS terminal dashboard renderer. All methods return plain strings. */
export class TerminalDashboard {
  /** Single-line status bar with key metrics. */
  renderStatusBar(data: DashboardData): string {
    const { uptime, version, paneCount, taskCount } = data.status;
    const health = data.raas.health === "healthy" ? c(A.green, "healthy") : c(A.red, data.raas.health);
    const hrs = Math.floor(uptime / 3600);
    const mins = Math.floor((uptime % 3600) / 60);
    const uptimeStr = `${hrs}h${mins}m`;
    return (
      c(A.bgBlue + A.bold, " OpenClaw ") +
      ` v${version}  ` +
      c(A.cyan, `⏱ ${uptimeStr}`) +
      `  panes:${c(A.white, String(paneCount))}` +
      `  tasks:${c(A.white, String(taskCount))}` +
      `  raas:${health}` +
      `  agi:${c(A.yellow, String(data.agiScore.score))}`
    );
  }

  /** Grid layout showing pane states (2-column). */
  renderPaneGrid(panes: PaneInfo[]): string {
    const rows: string[] = [];
    for (let i = 0; i < panes.length; i += 2) {
      const left = panes[i];
      const right = panes[i + 1];
      const fmtPane = (p: PaneInfo): string =>
        `${STATE_ICON[p.state] ?? "?"} ${c(A.cyan, p.id.padEnd(8))} ${p.provider.padEnd(8)} ${c(A.dim, p.project)}`;
      const row = right ? `${fmtPane(left).padEnd(40)}  ${fmtPane(right)}` : fmtPane(left);
      rows.push(row);
    }
    return box("Panes", rows.length ? rows : [c(A.dim, "No panes registered")]);
  }

  /** Task list with status icons. */
  renderTaskList(tasks: TaskEntry[]): string {
    const lines = tasks.length
      ? tasks.map(
          (t) =>
            `${TASK_ICON[t.status] ?? "?"} ${c(A.white, t.name.slice(0, 28).padEnd(28))} ${c(A.dim, t.assignedPane)}`
        )
      : [c(A.dim, "No tasks")];
    return box("Tasks", lines);
  }

  /** Combine all sections into a full dashboard view. */
  renderFullDashboard(data: DashboardData): string {
    const bar = this.renderStatusBar(data);
    const panes = this.renderPaneGrid(data.panes);
    const tasks = this.renderTaskList(data.tasks);
    const raasLine = `Tenants: ${data.raas.tenants}  Revenue: $${data.raas.revenue}  Health: ${data.raas.health}`;
    const raas = box("RaaS", [raasLine]);
    const agi = box("AGI Evolution", [
      `Score: ${c(A.yellow, String(data.agiScore.score))}  Capabilities: ${data.agiScore.capabilitiesCount}`,
    ]);
    return [bar, "", panes, "", tasks, "", raas, "", agi].join("\n");
  }

  /** Compact single-line summary. */
  renderCompactView(data: DashboardData): string {
    const running = data.panes.filter((p) => p.state === "running").length;
    const active = data.tasks.filter((t) => t.status === "active").length;
    return (
      c(A.bold, "OpenClaw") +
      ` v${data.status.version}` +
      ` | panes ${running}/${data.panes.length} running` +
      ` | tasks active:${active} total:${data.tasks.length}` +
      ` | agi:${data.agiScore.score}` +
      ` | raas:${data.raas.health}`
    );
  }
}
