import type { Brand, LicenseTier } from '../core/tiers.js';
import { LicenseGate } from '../core/gate.js';

export interface ExpressMiddlewareOptions {
  brand: Brand;
  minTier?: string;
  featureMap?: Record<string, string>;
}

// Generic RequestHandler — no express dep required
export type RequestHandler = (req: any, res: any, next: any) => void;

/**
 * Express-compatible middleware that enforces license checks.
 * Checks X-License-Key header first, then ?key= query param.
 */
export function licenseMiddleware(options: ExpressMiddlewareOptions): RequestHandler {
  const gate = new LicenseGate({ brand: options.brand });

  return (req: any, res: any, next: any): void => {
    const licenseKey: string =
      (req.headers?.['x-license-key'] as string | undefined) ??
      (req.query?.key as string | undefined) ??
      '';

    if (!licenseKey) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'License key required. Provide X-License-Key header or ?key= query param.',
      });
      return;
    }

    // Resolve required tier: featureMap by route path, then minTier, then default
    const routePath: string = req.path ?? req.url ?? '';
    const requiredTier = (
      options.featureMap?.[routePath] ??
      options.minTier ??
      'starter'
    ) as LicenseTier;

    const result = gate.canAccess(routePath, requiredTier);

    if (!result.allowed) {
      res.status(403).json({
        error: 'Forbidden',
        message: result.reason ?? 'Insufficient license tier',
        requiredTier,
        currentTier: result.tier ?? null,
      });
      return;
    }

    // Attach license info to request for downstream handlers
    req.license = {
      key: licenseKey,
      tier: result.tier,
      brand: options.brand,
    };

    next();
  };
}
