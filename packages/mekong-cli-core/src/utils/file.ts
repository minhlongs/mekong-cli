import { readFile, writeFile, mkdir, access, stat } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { ok, err, type Result } from '../types/common.js';

/** Read file content, return Result */
export async function readFileContent(filePath: string): Promise<Result<string>> {
  try {
    const content = await readFile(resolve(filePath), 'utf-8');
    return ok(content);
  } catch (error) {
    return err(error instanceof Error ? error : new Error(String(error)));
  }
}

/** Write file content, creating directories if needed */
export async function writeFileContent(filePath: string, content: string): Promise<Result<void>> {
  try {
    const resolved = resolve(filePath);
    await mkdir(dirname(resolved), { recursive: true });
    await writeFile(resolved, content, 'utf-8');
    return ok(undefined);
  } catch (error) {
    return err(error instanceof Error ? error : new Error(String(error)));
  }
}

/** Check if file exists */
export async function fileExists(filePath: string): Promise<boolean> {
  try {
    await access(resolve(filePath));
    return true;
  } catch {
    return false;
  }
}

/** Get file size in bytes */
export async function fileSize(filePath: string): Promise<Result<number>> {
  try {
    const stats = await stat(resolve(filePath));
    return ok(stats.size);
  } catch (error) {
    return err(error instanceof Error ? error : new Error(String(error)));
  }
}

/** Resolve path relative to project root */
export function resolveProjectPath(projectRoot: string, ...paths: string[]): string {
  return join(resolve(projectRoot), ...paths);
}
