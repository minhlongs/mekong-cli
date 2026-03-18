import { execSync } from 'node:child_process';

export interface DiscoveredCli {
  name: string;
  binary: string;
  path: string;
  version: string | null;
}

const KNOWN_BINARIES: Record<string, string> = {
  claude: 'claude',
  gemini: 'gemini',
  qwen: 'qwen',
  blackbox: 'blackbox',
};

function resolveWhich(binary: string): string | null {
  try {
    return execSync(`which ${binary}`, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return null;
  }
}

function resolveVersion(binary: string): string | null {
  try {
    return execSync(`${binary} --version 2>/dev/null`, {
      encoding: 'utf8',
      timeout: 3000,
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
  } catch {
    return null;
  }
}

export function discoverClis(): DiscoveredCli[] {
  const results: DiscoveredCli[] = [];
  for (const [name, binary] of Object.entries(KNOWN_BINARIES)) {
    const path = resolveWhich(binary);
    if (path !== null) {
      results.push({ name, binary, path, version: resolveVersion(binary) });
    }
  }
  return results;
}

export function getInstalledProviders(): string[] {
  return discoverClis().map((c) => c.name);
}
