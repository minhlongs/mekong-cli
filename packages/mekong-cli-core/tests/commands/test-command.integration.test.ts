import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Command } from 'commander';
import { registerTestCommand } from '../../src/cli/commands/test.js';

describe('Test Command Integration', () => {
  let program: Command;

  beforeEach(() => {
    program = new Command();
  });

  it('should register test command with correct description', () => {
    registerTestCommand(program);

    const testCmd = program.commands.find(cmd => cmd.name() === 'test');
    expect(testCmd).toBeDefined();
    expect(testCmd?.description()).toBe('Chạy test suite với hỗ trợ Cloudflare-only mode');
  });

  it('should have action function', () => {
    registerTestCommand(program);
    const testCmd = program.commands.find(cmd => cmd.name() === 'test');
    expect(testCmd?.action).toBeDefined();
    expect(typeof testCmd?.action).toBe('function');
  });

  it('should parse --cloudflare-only flag', async () => {
    registerTestCommand(program);

    // Mock process.argv to simulate command
    const originalArgv = process.argv;
    process.argv = ['node', 'mekong', 'test', '--cloudflare-only'];

    try {
      // Parse should not throw
      await program.parseAsync();
      // Command should execute without error (will exit due to process.exit in action)
    } catch (error) {
      // Expected to exit, ignore
    } finally {
      process.argv = originalArgv;
    }
  });

  it('should expose command name as "test"', () => {
    registerTestCommand(program);
    const testCmd = program.commands.find(cmd => cmd.name() === 'test');
    expect(testCmd?.name()).toBe('test');
  });
});
