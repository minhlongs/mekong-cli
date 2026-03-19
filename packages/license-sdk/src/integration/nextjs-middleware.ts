import type { Brand, LicenseTier } from '../core/tiers.js';
import { LicenseGate } from '../core/gate.js';

export interface NextjsOptions {
  brand: Brand;
  minTier?: string;
  protectedPaths?: string[];
}

export interface LicenseCheckResult {
  allowed: boolean;
  tier: string;
  response?: object;
}

/**
 * Next.js middleware helper that checks license from cookie or header.
 * Returns a plain object so callers can construct a NextResponse themselves.
 *
 * Usage in middleware.ts:
 *   const result = withLicenseCheck(opts)(request)
 *   if (!result.allowed) return NextResponse.json(result.response, { status: 403 })
 */
export function withLicenseCheck(
  options: NextjsOptions
): (req: any) => LicenseCheckResult {
  const gate = new LicenseGate({ brand: options.brand });
  const minTier = (options.minTier ?? 'starter') as LicenseTier;

  return (req: any): LicenseCheckResult => {
    const pathname: string =
      req.nextUrl?.pathname ?? req.url ?? '';

    // Skip check if path is not protected
    if (
      options.protectedPaths &&
      options.protectedPaths.length > 0 &&
      !options.protectedPaths.some((p) => pathname.startsWith(p))
    ) {
      return { allowed: true, tier: 'free' };
    }

    // Extract key from cookie then header
    const cookieKey: string =
      req.cookies?.get?.('openclaw-license')?.value ??
      req.cookies?.['openclaw-license'] ??
      '';

    const headerKey: string =
      req.headers?.get?.('x-license-key') ??
      req.headers?.['x-license-key'] ??
      '';

    const licenseKey = cookieKey || headerKey;

    if (!licenseKey) {
      return {
        allowed: false,
        tier: 'none',
        response: {
          error: 'Unauthorized',
          message: 'License key required. Set openclaw-license cookie or X-License-Key header.',
        },
      };
    }

    const result = gate.canAccess(pathname, minTier);

    if (!result.allowed) {
      return {
        allowed: false,
        tier: result.tier ?? 'unknown',
        response: {
          error: 'Forbidden',
          message: result.reason ?? 'Insufficient license tier',
          requiredTier: minTier,
          currentTier: result.tier ?? null,
        },
      };
    }

    return {
      allowed: true,
      tier: result.tier ?? minTier,
    };
  };
}
