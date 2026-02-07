/**
 * Input validation utilities for CLI arguments and configuration
 */

import { ValidationError } from './errors';

/**
 * Validates GitHub Personal Access Token format
 */
export function validateGitHubToken(token: string): void {
  if (!token) {
    throw new ValidationError('GitHub token is required');
  }

  // GitHub tokens start with specific prefixes
  const validPrefixes = ['ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_'];
  const hasValidPrefix = validPrefixes.some(prefix => token.startsWith(prefix));

  if (!hasValidPrefix) {
    throw new ValidationError(
      'Invalid GitHub token format. Token should start with ghp_, gho_, ghu_, ghs_, or ghr_'
    );
  }

  // Minimum length check (GitHub tokens are typically 40+ chars)
  if (token.length < 20) {
    throw new ValidationError('GitHub token appears too short. Please verify your token.');
  }
}

/**
 * Validates owner name format
 */
export function validateOwner(owner: string): void {
  if (!owner) {
    throw new ValidationError('Owner name is required');
  }

  // GitHub usernames/org names: alphanumeric + hyphens, max 39 chars
  const ownerRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,38}[a-zA-Z0-9])?$/;
  if (!ownerRegex.test(owner)) {
    throw new ValidationError(
      'Invalid owner name. Must be alphanumeric with hyphens, max 39 characters.'
    );
  }
}

/**
 * Validates project number
 */
export function validateProjectNumber(projectNumber: number): void {
  if (!Number.isInteger(projectNumber) || projectNumber < 1) {
    throw new ValidationError('Project number must be a positive integer');
  }
}

/**
 * Validates local file path
 */
export function validateLocalPath(localPath: string): void {
  if (!localPath) {
    throw new ValidationError('Local file path is required');
  }

  // Must end with .json
  if (!localPath.endsWith('.json')) {
    throw new ValidationError('Local file path must end with .json');
  }

  // Check for path traversal attempts
  if (localPath.includes('..')) {
    throw new ValidationError('Local file path cannot contain ".." (path traversal)');
  }
}

/**
 * Sanitizes user input to prevent injection attacks
 */
export function sanitizeInput(input: string): string {
  // Remove control characters and non-printable characters
  return input.replace(/[\x00-\x1F\x7F]/g, '').trim();
}

/**
 * Validates JSON file content structure
 */
export function validateTaskStoreStructure(data: any): void {
  if (typeof data !== 'object' || data === null) {
    throw new ValidationError('Invalid JSON: must be an object');
  }

  if (!Array.isArray(data.tasks)) {
    throw new ValidationError('Invalid JSON: "tasks" must be an array');
  }

  if (!Array.isArray(data.epics)) {
    throw new ValidationError('Invalid JSON: "epics" must be an array');
  }

  // Validate each task has required fields
  for (const task of data.tasks) {
    if (!task.id || !task.title || !task.status) {
      throw new ValidationError(
        `Invalid task structure: missing required fields (id, title, status)`
      );
    }
  }
}
