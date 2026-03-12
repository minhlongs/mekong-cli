import type { Result } from '../types/common.js';
import { ok, err, MekongError } from '../types/common.js';

/** Validate that a string is non-empty */
export function validateNonEmpty(value: string, fieldName: string): Result<string, MekongError> {
  if (!value || value.trim().length === 0) {
    return err(new MekongError(
      `${fieldName} must not be empty`,
      'VALIDATION_ERROR',
      true,
      { field: fieldName }
    ));
  }
  return ok(value.trim());
}

/** Validate duration string (e.g., "5s", "30m", "1h") and return ms */
export function parseDuration(duration: string): Result<number, MekongError> {
  const match = duration.match(/^(\d+(?:\.\d+)?)\s*(ms|s|m|h)$/);
  if (!match) {
    return err(new MekongError(
      `Invalid duration format: ${duration}. Use format like "5s", "30m", "1h"`,
      'VALIDATION_ERROR',
      true,
      { value: duration }
    ));
  }

  const value = parseFloat(match[1]);
  const unit = match[2];

  const multipliers: Record<string, number> = {
    ms: 1,
    s: 1000,
    m: 60000,
    h: 3600000,
  };

  return ok(value * multipliers[unit]);
}

/** Validate that a value is within range */
export function validateRange(
  value: number,
  min: number,
  max: number,
  fieldName: string
): Result<number, MekongError> {
  if (value < min || value > max) {
    return err(new MekongError(
      `${fieldName} must be between ${min} and ${max}, got ${value}`,
      'VALIDATION_ERROR',
      true,
      { field: fieldName, value, min, max }
    ));
  }
  return ok(value);
}
