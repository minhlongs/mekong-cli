import { execSync } from 'node:child_process';

export interface VersionReport {
  name: string;
  currentVersion: string;
  command: string;
}

export interface BreakingChange {
  name: string;
  from: string;
  to: string;
  severity: 'major' | 'minor' | 'patch';
}

const VERSION_COMMANDS: Array<{ name: string; command: string; pattern: RegExp }> = [
  { name: 'node', command: 'node --version', pattern: /v?(\d+\.\d+\.\d+)/ },
  { name: 'npm', command: 'npm --version', pattern: /(\d+\.\d+\.\d+)/ },
  { name: 'git', command: 'git --version', pattern: /(\d+\.\d+\.\d+)/ },
  { name: 'python3', command: 'python3 --version', pattern: /(\d+\.\d+\.\d+)/ },
  { name: 'tsc', command: 'tsc --version', pattern: /(\d+\.\d+\.\d+)/ },
  { name: 'claude', command: 'claude --version', pattern: /(\d+\.\d+\.\d+)/ },
  { name: 'gemini', command: 'gemini --version', pattern: /(\d+\.\d+\.\d+)/ },
];

function runCommand(cmd: string): string {
  try {
    return execSync(cmd, { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'stdout' in err) {
      return String((err as { stdout: unknown }).stdout).trim();
    }
    return '';
  }
}

function extractVersion(output: string, pattern: RegExp): string {
  const match = output.match(pattern);
  return match ? match[1] : 'unknown';
}

export function checkVersions(): VersionReport[] {
  return VERSION_COMMANDS.map(({ name, command, pattern }) => ({
    name,
    currentVersion: extractVersion(runCommand(command), pattern),
    command,
  }));
}

function parseMajor(version: string): number {
  if (version === 'unknown') return -1;
  return parseInt(version.split('.')[0] ?? '0', 10);
}

function parseMinor(version: string): number {
  if (version === 'unknown') return -1;
  return parseInt(version.split('.')[1] ?? '0', 10);
}

function getSeverity(from: string, to: string): BreakingChange['severity'] {
  const fromMajor = parseMajor(from);
  const toMajor = parseMajor(to);
  if (fromMajor !== toMajor && fromMajor !== -1 && toMajor !== -1) return 'major';
  const fromMinor = parseMinor(from);
  const toMinor = parseMinor(to);
  if (fromMinor !== toMinor) return 'minor';
  return 'patch';
}

export function detectBreakingChanges(previous: VersionReport[], current: VersionReport[]): BreakingChange[] {
  const currentMap = new Map(current.map((r) => [r.name, r.currentVersion]));
  const changes: BreakingChange[] = [];

  for (const prev of previous) {
    const curr = currentMap.get(prev.name);
    if (!curr || curr === prev.currentVersion) continue;
    const severity = getSeverity(prev.currentVersion, curr);
    if (severity === 'major') {
      changes.push({ name: prev.name, from: prev.currentVersion, to: curr, severity });
    }
  }
  return changes;
}

export function generateMigrationGuide(changes: BreakingChange[]): string {
  if (changes.length === 0) return '# Migration Guide\n\nNo breaking changes detected.\n';

  const lines = [
    '# Migration Guide',
    '',
    '## Breaking Changes Detected',
    '',
  ];

  for (const change of changes) {
    lines.push(
      `### ${change.name}: ${change.from} → ${change.to}`,
      `- **Severity**: ${change.severity}`,
      `- **Action**: Review the ${change.name} changelog for breaking changes between v${change.from} and v${change.to}.`,
      `- **Steps**: Update configs, check deprecations, run test suite after upgrade.`,
      '',
    );
  }

  return lines.join('\n');
}
