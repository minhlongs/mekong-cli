/**
 * Minimal TOML parser — supports venture.toml subset
 */

export interface ParsedToml {
  [section: string]: Record<string, string>;
}

export function parseToml(content: string): ParsedToml {
  const result: ParsedToml = {};
  let current = '';
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const sectionMatch = trimmed.match(/^\[([^\]]+)\]$/);
    if (sectionMatch) {
      current = sectionMatch[1].trim();
      if (!result[current]) result[current] = {};
      continue;
    }
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx < 0) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    let value = trimmed.slice(eqIdx + 1).trim();
    // Strip inline comments outside quoted strings
    if (!value.startsWith('"') && !value.startsWith("'")) {
      const commentIdx = value.indexOf(' #');
      if (commentIdx >= 0) value = value.slice(0, commentIdx).trim();
    }
    // Unquote
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    result[current][key] = value;
  }
  return result;
}
