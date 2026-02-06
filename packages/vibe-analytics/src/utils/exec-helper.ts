import { execFileSync } from 'child_process';

export function execGitCommand(args: string[]): string {
  try {
    return execFileSync('git', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch (error) {
    return '';
  }
}
