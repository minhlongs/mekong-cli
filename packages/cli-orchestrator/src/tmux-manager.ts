import { execSync } from 'node:child_process';

export type PaneInfo = {
  id: number;
  provider: string;
  createdAt: Date;
  session: string;
};

export type PaneStatus = {
  paneId: number;
  provider: string;
  state: 'idle' | 'busy' | 'error' | 'dead';
  lastOutput: string;
};

export type HealthResult = {
  paneId: number;
  healthy: boolean;
  issue?: string;
};

export class TmuxManager {
  private panes = new Map<string, PaneInfo[]>(); // session -> panes
  private providerMap = new Map<number, string>(); // paneId -> provider
  private nextId = 1;

  createPane(session: string, provider: string): PaneInfo {
    const id = this.nextId++;
    try {
      execSync(`tmux new-window -t "${session}" -n "${provider}-${id}"`, { stdio: 'pipe' });
    } catch {
      // session may not exist or tmux unavailable — track in-memory only
    }

    const pane: PaneInfo = { id, provider, createdAt: new Date(), session };
    const list = this.panes.get(session) ?? [];
    list.push(pane);
    this.panes.set(session, list);
    this.providerMap.set(id, provider);
    return pane;
  }

  destroyPane(session: string, paneId: number): boolean {
    const list = this.panes.get(session);
    if (!list) return false;

    const idx = list.findIndex((p) => p.id === paneId);
    if (idx === -1) return false;

    try {
      execSync(`tmux kill-window -t "${session}:${paneId}"`, { stdio: 'pipe' });
    } catch {
      // best-effort
    }

    list.splice(idx, 1);
    this.providerMap.delete(paneId);
    return true;
  }

  assignProvider(paneId: number, provider: string): void {
    this.providerMap.set(paneId, provider);
    for (const list of this.panes.values()) {
      const pane = list.find((p) => p.id === paneId);
      if (pane) {
        pane.provider = provider;
        break;
      }
    }
  }

  getPaneStatus(session: string): PaneStatus[] {
    const list = this.panes.get(session) ?? [];
    return list.map((pane) => {
      let lastOutput = '';
      let state: PaneStatus['state'] = 'idle';

      try {
        lastOutput = execSync(`tmux capture-pane -t "${session}" -p`, { stdio: 'pipe' })
          .toString()
          .trim()
          .slice(-200);

        if (lastOutput.includes('Error') || lastOutput.includes('error')) state = 'error';
        else if (lastOutput.length > 0) state = 'busy';
      } catch {
        state = 'dead';
      }

      return { paneId: pane.id, provider: pane.provider, state, lastOutput };
    });
  }

  healthCheck(session: string): HealthResult[] {
    const statuses = this.getPaneStatus(session);
    return statuses.map((s) => {
      if (s.state === 'dead') return { paneId: s.paneId, healthy: false, issue: 'pane is dead' };
      if (s.state === 'error') return { paneId: s.paneId, healthy: false, issue: 'pane has errors' };
      return { paneId: s.paneId, healthy: true };
    });
  }

  listPanes(session: string): PaneInfo[] {
    return [...(this.panes.get(session) ?? [])];
  }
}
