import { watch } from 'node:fs';
import { join } from 'node:path';
import { scanCommands } from './scanner.js';
import type { CommandDefinition } from './scanner.js';

export interface WatchHandle {
  close(): void;
}

/**
 * Watch .claude/commands/ (and skills/) for changes and invoke onChange with
 * the updated full command list on each detected change.
 *
 * Uses a 200ms debounce to coalesce rapid filesystem events (e.g. editor saves).
 */
export function watchCommands(
  basePath: string,
  onChange: (cmds: CommandDefinition[]) => void
): WatchHandle {
  const commandsDir = join(basePath, '.claude', 'commands');
  const skillsDir = join(basePath, '.claude', 'skills');

  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  const handleChange = (): void => {
    if (debounceTimer !== null) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      debounceTimer = null;
      const cmds = scanCommands(basePath);
      onChange(cmds);
    }, 200);
  };

  const watchers: ReturnType<typeof watch>[] = [];

  try {
    watchers.push(
      watch(commandsDir, { recursive: false }, handleChange)
    );
  } catch {
    // directory may not exist — silently skip
  }

  try {
    watchers.push(
      watch(skillsDir, { recursive: true }, handleChange)
    );
  } catch {
    // directory may not exist — silently skip
  }

  return {
    close(): void {
      if (debounceTimer !== null) {
        clearTimeout(debounceTimer);
        debounceTimer = null;
      }
      for (const w of watchers) {
        try {
          w.close();
        } catch {
          // ignore close errors
        }
      }
    },
  };
}
