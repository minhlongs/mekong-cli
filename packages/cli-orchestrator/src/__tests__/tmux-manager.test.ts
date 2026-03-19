import { describe, it, expect, beforeEach, vi } from 'vitest';
import { TmuxManager } from '../tmux-manager.js';

// Mock execSync so tests never touch real tmux
vi.mock('node:child_process', () => ({
  execSync: vi.fn(() => Buffer.from('')),
}));

describe('TmuxManager', () => {
  let mgr: TmuxManager;
  const SESSION = 'test-session';

  beforeEach(() => {
    mgr = new TmuxManager();
  });

  describe('createPane', () => {
    it('returns PaneInfo with correct fields', () => {
      const pane = mgr.createPane(SESSION, 'claude');
      expect(pane.session).toBe(SESSION);
      expect(pane.provider).toBe('claude');
      expect(typeof pane.id).toBe('number');
      expect(pane.createdAt).toBeInstanceOf(Date);
    });

    it('assigns incrementing IDs', () => {
      const a = mgr.createPane(SESSION, 'claude');
      const b = mgr.createPane(SESSION, 'gemini');
      expect(b.id).toBe(a.id + 1);
    });
  });

  describe('destroyPane', () => {
    it('returns true when pane exists', () => {
      const pane = mgr.createPane(SESSION, 'claude');
      expect(mgr.destroyPane(SESSION, pane.id)).toBe(true);
    });

    it('returns false for unknown pane', () => {
      expect(mgr.destroyPane(SESSION, 9999)).toBe(false);
    });

    it('removes pane from listPanes', () => {
      const pane = mgr.createPane(SESSION, 'claude');
      mgr.destroyPane(SESSION, pane.id);
      expect(mgr.listPanes(SESSION)).toHaveLength(0);
    });
  });

  describe('assignProvider', () => {
    it('updates provider on existing pane', () => {
      const pane = mgr.createPane(SESSION, 'claude');
      mgr.assignProvider(pane.id, 'gemini');
      const list = mgr.listPanes(SESSION);
      expect(list[0]?.provider).toBe('gemini');
    });
  });

  describe('listPanes', () => {
    it('returns empty array for unknown session', () => {
      expect(mgr.listPanes('nonexistent')).toEqual([]);
    });

    it('lists all panes in session', () => {
      mgr.createPane(SESSION, 'claude');
      mgr.createPane(SESSION, 'gemini');
      expect(mgr.listPanes(SESSION)).toHaveLength(2);
    });
  });

  describe('getPaneStatus', () => {
    it('returns one status per pane', () => {
      mgr.createPane(SESSION, 'claude');
      mgr.createPane(SESSION, 'qwen');
      const statuses = mgr.getPaneStatus(SESSION);
      expect(statuses).toHaveLength(2);
    });

    it('returns dead state when execSync throws', async () => {
      const { execSync } = await import('node:child_process');
      mgr.createPane(SESSION, 'claude');
      // Make capture-pane call throw
      vi.mocked(execSync).mockImplementation(() => { throw new Error('no tmux'); });
      const [status] = mgr.getPaneStatus(SESSION);
      expect(status?.state).toBe('dead');
      vi.mocked(execSync).mockReset();
      vi.mocked(execSync).mockReturnValue(Buffer.from(''));
    });
  });

  describe('healthCheck', () => {
    it('marks dead pane as unhealthy', async () => {
      const { execSync } = await import('node:child_process');
      vi.mocked(execSync).mockImplementation(() => { throw new Error('no tmux'); });
      mgr.createPane(SESSION, 'claude');
      const [result] = mgr.healthCheck(SESSION);
      expect(result?.healthy).toBe(false);
      expect(result?.issue).toBeDefined();
    });
  });
});
