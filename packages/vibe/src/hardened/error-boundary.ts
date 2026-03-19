// Dynamic import to avoid module resolution issues during build
async function getLogger() {
  // @ts-ignore - @mekong/shared exists but type resolution may fail
  const { logger } = await import('@mekong/shared');
  return logger;
}

/**
 * 🛡️ VIBE Hardened - Error Boundary Patterns
 */
export interface ErrorState {
    hasError: boolean;
    error?: Error;
    errorInfo?: string;
    timestamp: Date;
}

export function createErrorState(error: Error): ErrorState {
    return {
        hasError: true,
        error,
        errorInfo: error.stack,
        timestamp: new Date(),
    };
}

export async function logError(error: ErrorState): Promise<void> {
    const logger = await getLogger();
    logger.error(`[VIBE Error] ${error.error?.message}`, {
        stack: error.errorInfo,
        timestamp: error.timestamp.toISOString(),
    });
}
