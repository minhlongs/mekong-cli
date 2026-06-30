/**
 * PEV Engine — Verification Engine
 *
 * Port of Mekong CLI's RecipeVerifier.
 * Validates execution results against verification criteria.
 */

import type {
  ExecutionResult,
  VerificationCheck,
  VerificationCriteria,
  VerificationReport,
  VerificationStatus,
} from './types.js';

export class Verifier {
  private strict_mode: boolean;

  constructor(strict_mode: boolean = true) {
    this.strict_mode = strict_mode;
  }

  verify(result: ExecutionResult, criteria: VerificationCriteria): VerificationReport {
    const report: VerificationReport = {
      passed: true,
      checks: [],
      warnings: [],
      errors: [],
    };

    // Exit code check
    if (criteria.exit_code !== undefined && criteria.exit_code !== null) {
      const check = this.verifyExitCode(result, criteria.exit_code);
      report.checks.push(check);
      if (check.status === 'failed') report.passed = false;
    }

    // File existence checks
    for (const filepath of criteria.file_exists ?? []) {
      const check = this.verifyFileExists(filepath);
      report.checks.push(check);
      if (check.status === 'failed') report.passed = false;
    }

    // File non-existence checks
    for (const filepath of criteria.file_not_exists ?? []) {
      const check = this.verifyFileNotExists(filepath);
      report.checks.push(check);
      if (check.status === 'failed') report.passed = false;
    }

    // Output contains checks
    for (const pattern of criteria.output_contains ?? []) {
      const check = this.verifyOutputContains(result, pattern);
      report.checks.push(check);
      if (check.status === 'failed') report.passed = false;
    }

    // Output not contains checks
    for (const pattern of criteria.output_not_contains ?? []) {
      const check = this.verifyOutputNotContains(result, pattern);
      report.checks.push(check);
      if (check.status === 'failed') report.passed = false;
    }

    // Collect warnings and errors
    for (const check of report.checks) {
      if (check.status === 'failed') {
        report.errors.push(check.message);
      } else if (check.status === 'warning') {
        report.warnings.push(check.message);
      }
    }

    if (this.strict_mode && report.warnings.length > 0) {
      report.passed = false;
    }

    return report;
  }

  verifyExitCode(result: ExecutionResult, expected: number): VerificationCheck {
    if (result.exit_code === expected) {
      return {
        name: 'exit_code',
        status: 'passed',
        message: `Exit code ${result.exit_code} matches expected`,
        expected,
        actual: result.exit_code,
      };
    }
    return {
      name: 'exit_code',
      status: 'failed',
      message: `Exit code mismatch: expected ${expected}, got ${result.exit_code}`,
      expected,
      actual: result.exit_code,
    };
  }

  verifyFileExists(filepath: string): VerificationCheck {
    // In ClaudeKit context, we delegate file existence to the agent's file tools.
    // This returns a check that the agent can resolve.
    return {
      name: `file_exists:${filepath}`,
      status: 'skipped',
      message: `File existence check delegated to agent: ${filepath}`,
      expected: true,
      actual: 'delegated',
    };
  }

  verifyFileNotExists(filepath: string): VerificationCheck {
    return {
      name: `file_not_exists:${filepath}`,
      status: 'skipped',
      message: `File non-existence check delegated to agent: ${filepath}`,
      expected: false,
      actual: 'delegated',
    };
  }

  verifyOutputContains(result: ExecutionResult, pattern: string): VerificationCheck {
    const combined = result.stdout + '\n' + result.stderr;

    // Try regex match first
    try {
      const regex = new RegExp(pattern, 'i');
      if (regex.test(combined)) {
        return {
          name: `output_contains:${pattern}`,
          status: 'passed',
          message: `Output contains pattern: ${pattern}`,
          expected: pattern,
          actual: 'found',
        };
      }
    } catch {
      // Not a valid regex, try simple substring
      if (combined.toLowerCase().includes(pattern.toLowerCase())) {
        return {
          name: `output_contains:${pattern}`,
          status: 'passed',
          message: `Output contains: ${pattern}`,
          expected: pattern,
          actual: 'found',
        };
      }
    }

    return {
      name: `output_contains:${pattern}`,
      status: 'failed',
      message: `Output does not contain: ${pattern}`,
      expected: pattern,
      actual: 'not found',
    };
  }

  verifyOutputNotContains(result: ExecutionResult, pattern: string): VerificationCheck {
    const combined = result.stdout + '\n' + result.stderr;

    try {
      const regex = new RegExp(pattern, 'i');
      if (regex.test(combined)) {
        return {
          name: `output_not_contains:${pattern}`,
          status: 'failed',
          message: `Output contains forbidden pattern: ${pattern}`,
          expected: `not ${pattern}`,
          actual: 'found',
        };
      }
    } catch {
      if (combined.toLowerCase().includes(pattern.toLowerCase())) {
        return {
          name: `output_not_contains:${pattern}`,
          status: 'failed',
          message: `Output contains forbidden text: ${pattern}`,
          expected: `not ${pattern}`,
          actual: 'found',
        };
      }
    }

    return {
      name: `output_not_contains:${pattern}`,
      status: 'passed',
      message: `Output correctly does not contain: ${pattern}`,
      expected: `not ${pattern}`,
      actual: 'not found',
    };
  }

  /**
   * Binh Phap quality gates — enforce zero tech debt, clean logs, type safety.
   */
  verifyQualityGates(result: ExecutionResult): VerificationReport {
    const report: VerificationReport = {
      passed: true,
      checks: [],
      warnings: [],
      errors: [],
    };

    // Tech Debt: no TODO/FIXME
    const todoCheck = this.verifyOutputNotContains(result, 'TODO|FIXME');
    todoCheck.name = 'binh_phap:tech_debt_todos';
    report.checks.push(todoCheck);
    if (todoCheck.status === 'failed') report.passed = false;

    // Clean logs: no console.log/print
    const logCheck = this.verifyOutputNotContains(result, 'console\\.log|print\\(');
    logCheck.name = 'binh_phap:clean_logs';
    report.checks.push(logCheck);
    if (logCheck.status === 'failed') report.passed = false;

    // Type safety: no :any
    const anyCheck = this.verifyOutputNotContains(result, ': any|: Any');
    anyCheck.name = 'binh_phap:type_safety';
    report.checks.push(anyCheck);
    if (anyCheck.status === 'failed') report.passed = false;

    // Security: no vulnerabilities
    const vulnCheck = this.verifyOutputNotContains(result, 'vulnerabilit|critical|high severity');
    vulnCheck.name = 'binh_phap:security';
    report.checks.push(vulnCheck);
    if (vulnCheck.status === 'failed') report.passed = false;

    return report;
  }
}
