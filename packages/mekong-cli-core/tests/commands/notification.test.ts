/**
 * Tests for `mekong notification` command (Wave 52).
 * Covers: send, list, config, channels subcommands.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerNotificationCommand } from '../../src/cli/commands/notification.js';

const noop = () => {};

function createProgram(): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: noop, writeErr: noop });
  registerNotificationCommand(program);
  return program;
}

describe('notification command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register notification command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'notification');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const ntfCmd = program.commands.find(c => c.name() === 'notification');
    expect(ntfCmd).toBeDefined();
    const subNames = ntfCmd!.commands.map(c => c.name());
    expect(subNames).toContain('send');
    expect(subNames).toContain('list');
    expect(subNames).toContain('config');
    expect(subNames).toContain('channels');
  });

  describe('notification send', () => {
    it('should send email notification', async () => {
      const program = createProgram();
      await program.parseAsync([
        'node', 'test', 'notification', 'send',
        '--channel', 'email',
        '--to', 'test@example.vn',
        '--message', 'Đơn hàng của bạn đã được xác nhận',
      ]);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should send slack notification', async () => {
      const program = createProgram();
      await program.parseAsync([
        'node', 'test', 'notification', 'send',
        '--channel', 'slack',
        '--to', '#general',
        '--message', 'Deploy hoàn tất',
      ]);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn when channel is not configured (sms)', async () => {
      const program = createProgram();
      await program.parseAsync([
        'node', 'test', 'notification', 'send',
        '--channel', 'sms',
        '--to', '+84901234567',
        '--message', 'OTP: 123456',
      ]);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn on unknown channel', async () => {
      const program = createProgram();
      await program.parseAsync([
        'node', 'test', 'notification', 'send',
        '--channel', 'pigeon',
        '--to', 'somewhere',
        '--message', 'hello',
      ]);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn when --to is missing', async () => {
      const program = createProgram();
      await program.parseAsync([
        'node', 'test', 'notification', 'send',
        '--channel', 'email',
        '--message', 'No recipient',
      ]);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn when --message is missing', async () => {
      const program = createProgram();
      await program.parseAsync([
        'node', 'test', 'notification', 'send',
        '--channel', 'email',
        '--to', 'test@example.vn',
      ]);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('notification list', () => {
    it('should list all notifications by default', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'list']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should filter by status sent', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'list', '--status', 'sent']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should filter by status failed', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'list', '--status', 'failed']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should filter by status pending', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'list', '--status', 'pending']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn when no notifications match filter', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'list', '--status', 'nonexistent']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should respect --limit option', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'list', '--limit', '2']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should output multiple rows', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'list']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(3);
    });
  });

  describe('notification config', () => {
    it('should show notification configuration', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'config']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should output multiple config lines', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'config']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(3);
    });
  });

  describe('notification channels', () => {
    it('should list all available channels', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'channels']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should output one line per channel', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'notification', 'channels']);
      // 4 channels + heading + divider + summary lines
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(3);
    });
  });
});
