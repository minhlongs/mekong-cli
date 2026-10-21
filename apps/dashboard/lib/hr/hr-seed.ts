/**
 * HR Tax & Social Security Configuration (SEA)
 */

export const TAX_BRACKETS: Record<string, { min: number; max: number; rate: number }[]> = {
  VN: [
    // Vietnam PIT
    { min: 0, max: 5000000, rate: 0.05 },
    { min: 5000000, max: 10000000, rate: 0.1 },
    { min: 10000000, max: 18000000, rate: 0.15 },
    { min: 18000000, max: 32000000, rate: 0.2 },
    { min: 32000000, max: 52000000, rate: 0.25 },
    { min: 52000000, max: 80000000, rate: 0.3 },
    { min: 80000000, max: Infinity, rate: 0.35 },
  ],
  TH: [
    // Thailand PIT
    { min: 0, max: 150000, rate: 0 },
    { min: 150000, max: 300000, rate: 0.05 },
    { min: 300000, max: 500000, rate: 0.1 },
    { min: 500000, max: 750000, rate: 0.15 },
    { min: 750000, max: 1000000, rate: 0.2 },
    { min: 1000000, max: 2000000, rate: 0.25 },
    { min: 2000000, max: 5000000, rate: 0.3 },
    { min: 5000000, max: Infinity, rate: 0.35 },
  ],
  ID: [
    // Indonesia PIT
    { min: 0, max: 60000000, rate: 0.05 },
    { min: 60000000, max: 250000000, rate: 0.15 },
    { min: 250000000, max: 500000000, rate: 0.25 },
    { min: 500000000, max: 5000000000, rate: 0.3 },
    { min: 5000000000, max: Infinity, rate: 0.35 },
  ],
}

export const SOCIAL_SECURITY_RATES: Record<string, { employee: number; employer: number }> = {
  VN: { employee: 0.105, employer: 0.215 },
  TH: { employee: 0.05, employer: 0.05 },
  ID: { employee: 0.02, employer: 0.0389 },
  SG: { employee: 0.2, employer: 0.17 },
  PH: { employee: 0.045, employer: 0.095 },
}
