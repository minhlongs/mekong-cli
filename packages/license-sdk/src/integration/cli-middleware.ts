import type { Brand, LicenseTier } from '../core/tiers.js';
import { LicenseGate } from '../core/gate.js';

export interface CliMiddlewareOptions {
  brand: Brand;
  featureMap?: Record<string, string>;
  onDenied?: (cmd: string) => void;
}

/**
 * Creates a Commander.js-compatible preAction hook that enforces license checks.
 * Attach via: program.hook('preAction', createCliLicenseMiddleware(opts))
 */
export function createCliLicenseMiddleware(
  options: CliMiddlewareOptions
): (command: any) => void {
  const gate = new LicenseGate({ brand: options.brand });

  return (command: any): void => {
    const cmdName: string =
      typeof command?.name === 'function' ? command.name() : String(command?.name ?? '');

    // Resolve required tier from featureMap, default to 'starter'
    const requiredTier = (options.featureMap?.[cmdName] ?? 'starter') as LicenseTier;

    const result = gate.canAccess(cmdName, requiredTier);

    if (!result.allowed) {
      if (options.onDenied) {
        options.onDenied(cmdName);
      } else {
        const reason = result.reason ?? 'License check failed';
        process.stderr.write(`[license] Access denied for '${cmdName}': ${reason}\n`);
        process.exit(1);
      }
    }
  };
}

/**
 * Method decorator that checks license before the decorated method runs.
 * Usage: @withLicense('openclaw', 'pro')
 */
export function withLicense(
  brand: Brand,
  minTier: LicenseTier
): (target: any, key: string, descriptor: PropertyDescriptor) => PropertyDescriptor {
  return function (
    _target: any,
    methodKey: string,
    descriptor: PropertyDescriptor
  ): PropertyDescriptor {
    const original = descriptor.value;

    descriptor.value = function (...args: any[]): any {
      const gate = new LicenseGate({ brand });
      const result = gate.canAccess(methodKey, minTier);

      if (!result.allowed) {
        const reason = result.reason ?? 'Insufficient license tier';
        throw new Error(`[license] ${reason}`);
      }

      return original.apply(this, args);
    };

    return descriptor;
  };
}
