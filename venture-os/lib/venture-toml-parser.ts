/**
 * Minimal TOML parser for venture.toml files.
 *
 * Supports only the subset we emit: [section] headers,
 * unquoted scalars, quoted strings, and inline comments.
 * Full TOML spec is overkill for this use case.
 */

export interface ParsedToml {
  [section: string]: Record<string, string | ParsedToml>;
}

export function parseToml(content: string): ParsedToml {
  const result: ParsedToml = {};
  let currentSection = '';

  for (const rawLine of content.split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;

    // [section]
    const sectionMatch = line.match(/^\[([^\]]+)\]$/);
    if (sectionMatch) {
      currentSection = sectionMatch[1].trim();
      if (!result[currentSection]) result[currentSection] = {};
      continue;
    }

    // key = value
    const eqIdx = line.indexOf('=');
    if (eqIdx < 0) continue;
    const rawKey = line.slice(0, eqIdx).trim();
    const rawValue = line.slice(eqIdx + 1).trim();

    // strip inline comment (only outside quoted strings)
    const value = stripComment(rawValue);

    const target = currentSection ? result[currentSection] : result;

    if (rawKey.includes('.')) {
      // dotted key → nested
      const [head, ...rest] = rawKey.split('.');
      ensureNested(target, head, rest.join('.')).value = value;
    } else {
      target[rawKey] = parseValue(value);
    }
  }

  return result;
}

function ensureNested(
  root: Record<string, unknown>,
  head: string,
  rest: string,
): Record<string, unknown> {
  let node = root[head];
  if (node && typeof node === 'object' && !Array.isArray(node)) return node as Record<string, unknown>;
  const created: Record<string, unknown> = {};
  root[head] = created;
  if (rest) ensureNested(created, rest, '');
  return created;
}

function stripComment(value: string): string {
  const inSingle = /^'/.test(value);
  const inDouble = /^"/.test(value);
  if (inSingle || inDouble) return value;

  // unquoted: strip # comment
  const idx = value.indexOf(' #');
  return idx >= 0 ? value.slice(0, idx).trim() : value;
}

function parseValue(raw: string): string {
  const trimmed = raw.trim();
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
      (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}
