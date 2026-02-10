import { readFile, writeFile, mkdir, access } from 'node:fs/promises';
import { dirname } from 'node:path';

/**
 * Read and parse a JSON file
 */
export async function readJson<T = unknown>(path: string): Promise<T> {
  const content = await readFile(path, 'utf-8');
  return JSON.parse(content) as T;
}

/**
 * Write data as JSON to a file
 */
export async function writeJson(
  path: string,
  data: unknown,
  options: { pretty?: boolean } = {}
): Promise<void> {
  const { pretty = true } = options;
  const content = pretty ? JSON.stringify(data, null, 2) : JSON.stringify(data);
  await writeFile(path, content, 'utf-8');
}

/**
 * Ensure a directory exists, creating it if necessary
 */
export async function ensureDir(path: string): Promise<void> {
  try {
    await mkdir(path, { recursive: true });
  } catch (error) {
    // Ignore EEXIST errors (directory already exists)
    if ((error as NodeJS.ErrnoException).code !== 'EEXIST') {
      throw error;
    }
  }
}

/**
 * Check if a file exists
 */
export async function fileExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

/**
 * Ensure the parent directory of a file exists
 */
export async function ensureParentDir(filePath: string): Promise<void> {
  const dir = dirname(filePath);
  await ensureDir(dir);
}
