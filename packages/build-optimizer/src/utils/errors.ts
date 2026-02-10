/**
 * Base error class for all build optimizer errors
 */
export class BuildOptimizerError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'BuildOptimizerError';
    
    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, BuildOptimizerError);
    }
  }
}

/**
 * Configuration-related errors
 */
export class ConfigError extends BuildOptimizerError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'CONFIG_ERROR', context);
    this.name = 'ConfigError';
  }
}

/**
 * Build execution errors
 */
export class BuildError extends BuildOptimizerError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'BUILD_ERROR', context);
    this.name = 'BuildError';
  }
}

/**
 * Agent execution errors
 */
export class AgentError extends BuildOptimizerError {
  constructor(
    message: string,
    public readonly agentName: string,
    context?: Record<string, unknown>
  ) {
    super(message, 'AGENT_ERROR', { ...context, agentName });
    this.name = 'AgentError';
  }
}

/**
 * Optimization failed errors
 */
export class OptimizationFailedError extends BuildOptimizerError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'OPTIMIZATION_FAILED', context);
    this.name = 'OptimizationFailedError';
  }
}

/**
 * Validation errors
 */
export class ValidationError extends BuildOptimizerError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'VALIDATION_ERROR', context);
    this.name = 'ValidationError';
  }
}
