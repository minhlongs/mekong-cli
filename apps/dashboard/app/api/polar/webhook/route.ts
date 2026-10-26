import { NextResponse } from 'next/server'

/**
 * HTTP 410 Gone — Polar.sh webhook endpoint permanently decommissioned.
 * Mekong CLI & Dashboard use Dual-Rail RaaS (VietQR Napas 247 + NOWPayments USDT).
 */
export async function POST() {
  return NextResponse.json(
    {
      error: 'polar_rail_decommissioned',
      message: 'Polar.sh payment rail is permanently decommissioned (HTTP 410 Gone). Use Dual-Rail VietQR or NOWPayments.',
    },
    { status: 410 }
  )
}

export async function GET() {
  return NextResponse.json(
    {
      error: 'polar_rail_decommissioned',
      message: 'Polar.sh payment rail is permanently decommissioned (HTTP 410 Gone).',
    },
    { status: 410 }
  )
}
