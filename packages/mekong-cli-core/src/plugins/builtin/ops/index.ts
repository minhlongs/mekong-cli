/**
 * Ops Plugin — Operations and maintenance commands.
 *
 * Provides: monitor, workflow, notification, backup, migration.
 *
 * To register this plugin with the main CLI, call registerOpsPlugin(program, engine).
 */

import type { Command } from 'commander';
import type { MekongEngine } from '../../core/index.js';

// Command modules (imported from core CLI commands)
import { registerMonitorCommand } from '../../cli/commands/monitor.js';
import { registerWorkflowCommand } from '../../cli/commands/workflow.js';
import { registerNotificationCommand } from '../../cli/commands/notification.js';
import { registerBackupCommand } from '../../cli/commands/backup.js';
import { registerMigrationCommand } from '../../cli/commands/migration.js';

export function registerOpsPlugin(program: Command, engine: MekongEngine): void {
  // Register all ops commands
  registerMonitorCommand(program, engine);
  registerWorkflowCommand(program, engine);
  registerNotificationCommand(program, engine);
  registerBackupCommand(program, engine);
  registerMigrationCommand(program, engine);
}

export const OPS_COMMANDS = [
  'monitor',
  'workflow',
  'notification',
  'backup',
  'migration'
];