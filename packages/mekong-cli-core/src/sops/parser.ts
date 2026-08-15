import { readFile } from 'node:fs/promises';
import { parse as parseYaml } from 'yaml';
import { SopDefinitionSchema, type SopDefinition } from '../types/sop.js';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';

/** Parse a SOP YAML file and validate with Zod */
export async function parseSopFile(filePath: string): Promise<Result<SopDefinition>> {
  try {
    const content = await readFile(filePath, 'utf-8');
    return parseSopYaml(content);
  } catch (error) {
    return err(new Error(`Failed to read SOP file: ${filePath} — ${error}`));
  }
}

/** Parse SOP from YAML string */
export function parseSopYaml(yamlContent: string): Result<SopDefinition> {
  try {
    const raw = parseYaml(yamlContent);
    const parsed = SopDefinitionSchema.parse(raw);
    return ok(parsed);
  } catch (error) {
    return err(new Error(`SOP validation failed: ${error instanceof Error ? error.message : String(error)}`));
  }
}
