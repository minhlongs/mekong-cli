export { createCliLicenseMiddleware, withLicense } from './cli-middleware.js';
export type { CliMiddlewareOptions } from './cli-middleware.js';

export { licenseMiddleware } from './express-middleware.js';
export type { ExpressMiddlewareOptions, RequestHandler } from './express-middleware.js';

export { withLicenseCheck } from './nextjs-middleware.js';
export type { NextjsOptions, LicenseCheckResult } from './nextjs-middleware.js';

export { createGate, activateFromEnv, requireAccess, issueTrialKey } from './gate-helpers.js';
export type { LicenseGateOptions, GateStatus } from './gate-helpers.js';
