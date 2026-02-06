export function safeJSONStringify(obj, replacer = null, space = 2) {
  const cache = new Set();
  return JSON.stringify(
    obj,
    (key, value) => {
      if (typeof value === 'object' && value !== null) {
        if (cache.has(value)) {
          return '[Circular]';
        }
        cache.add(value);
      }
      if (typeof value === 'bigint') {
        return value.toString();
      }
      if (replacer) {
        return replacer(key, value);
      }
      return value;
    },
    space
  );
}

export function safeJSONParse(str, fallback = null) {
  if (typeof str !== 'string') return fallback;
  try {
    return JSON.parse(str);
  } catch (e) {
    return fallback;
  }
}

export async function withRetry(fn, retries = 5, baseDelay = 100) {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (error) {
      // Retry on SQLite busy/locked errors
      const isBusy =
        error.message?.includes('database is locked') ||
        error.message?.includes('SQLITE_BUSY') ||
        error.code === 'P2034'; // Prisma transaction failed

      if (i === retries - 1 || !isBusy) throw error;

      const delay = baseDelay * Math.pow(2, i);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
