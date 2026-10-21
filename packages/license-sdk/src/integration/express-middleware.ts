import type { Brand, LicenseTier } from '../core/tiers.js';
import { LicenseGate } from '../core/gate.js';

export interface ExpressMiddlewareOptions {
  brand: Brand;
  minTier?: string;
  featureMap?: Record<string, string>;
}

export interface ExpressRequestLike {
  headers?: Record<string, string | string[] | undefined>;
  query?: Record<string, string | string[] | undefined>;
  path?: string;
  url?: string;
  license?: {
    key: string;
    tier?: LicenseTier;
    brand: Brand;
  };
}

export interface ExpressResponseLike {
  status: (code: number) => {
    json: (body: Record<string, unknown>) => unknown;
  };
}

export type ExpressNextFunction = (err?: unknown) => void;

// Generic RequestHandler — no express dep required
export type RequestHandler = (
  req: ExpressRequestLike,
  res: ExpressResponseLike,
  next: ExpressNextFunction
) => void;

/**
 * Express-compatible middleware that enforces license checks.
 * Checks X-License-Key header first, then ?key= query param.
 */
export function licenseMiddleware(options: ExpressMiddlewareOptions): RequestHandler {
  const gate = new LicenseGate({ brand: options.brand });

  return (
    req: ExpressRequestLike,
    res: ExpressResponseLike,
    next: ExpressNextFunction
  ): void => {
    const rawHeader = req.headers?.['x-license-key'];
    const rawQuery = req.query?.['key'];
    const headerVal = Array.isArray(rawHeader) ? rawHeader[0] : rawHeader;
    const queryVal = Array.isArray(rawQuery) ? rawQuery[0] : rawQuery;
    const licenseKey: string = headerVal ?? queryVal ?? '';

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
