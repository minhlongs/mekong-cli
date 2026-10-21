/**
 * Inventory License Tracking & Asset Valuation Summary
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { Asset, AssetStatus, AssetSummary, AssetType, LicenseInfo } from './inventory-types'

export async function createLicenseWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  license: Omit<LicenseInfo, 'id' | 'tenantId' | 'createdAt'>
): Promise<LicenseInfo> {
  const { data, error } = await supabase
    .from('licenses')
    .insert({
      tenant_id: tenantId,
      asset_id: license.assetId,
      name: license.name,
      vendor: license.vendor,
      license_key: license.licenseKey,
      seats: license.seats,
      used_seats: license.usedSeats,
      purchase_date: license.purchaseDate.toISOString(),
      expiry_date: license.expiryDate?.toISOString(),
      cost: license.cost,
      billing_cycle: license.billingCycle,
      status: license.status,
    })
    .select()
    .single()

  if (error) throw new Error(`Failed to create license: ${error.message}`)

  return {
    id: data.id,
    tenantId: data.tenant_id,
    assetId: data.asset_id,
    name: data.name,
    vendor: data.vendor,
    licenseKey: data.license_key,
    seats: data.seats,
    usedSeats: data.used_seats,
    purchaseDate: new Date(data.purchase_date),
    expiryDate: data.expiry_date ? new Date(data.expiry_date) : undefined,
    cost: data.cost,
    billingCycle: data.billing_cycle,
    status: data.status,
    createdAt: new Date(data.created_at),
  }
}

export async function listLicensesWithClient(
  supabase: SupabaseClient,
  tenantId: string
): Promise<LicenseInfo[]> {
  const { data, error } = await supabase
    .from('licenses')
    .select('*')
    .eq('tenant_id', tenantId)
    .order('expiry_date', { ascending: true })

  if (error) throw new Error(`Failed to list licenses: ${error.message}`)

  return (data || []).map(l => ({
    id: l.id,
    tenantId: l.tenant_id,
    assetId: l.asset_id,
    name: l.name,
    vendor: l.vendor,
    licenseKey: l.license_key,
    seats: l.seats,
    usedSeats: l.used_seats,
    purchaseDate: new Date(l.purchase_date),
    expiryDate: l.expiry_date ? new Date(l.expiry_date) : undefined,
    cost: l.cost,
    billingCycle: l.billing_cycle,
    status: l.status,
    createdAt: new Date(l.created_at),
  }))
}

export function computeAssetSummary(assets: Asset[]): AssetSummary {
  const byType: Record<AssetType, number> = {
    hardware: 0,
    software: 0,
    subscription: 0,
    digital: 0,
    other: 0,
  }

  const byStatus: Record<AssetStatus, number> = {
    active: 0,
    in_use: 0,
    maintenance: 0,
    retired: 0,
    disposed: 0,
  }

  let totalValue = 0
  let expiringThisMonth = 0
  const endOfMonth = new Date()
  endOfMonth.setMonth(endOfMonth.getMonth() + 1)
  endOfMonth.setDate(0)

  for (const asset of assets) {
    byType[asset.type]++
    byStatus[asset.status]++
    totalValue += asset.currentValue || asset.purchasePrice || 0

    if (asset.expiryDate && asset.expiryDate <= endOfMonth) {
      expiringThisMonth++
    }
  }

  return {
    totalAssets: assets.length,
    byType,
    byStatus,
    totalValue,
    expiringThisMonth,
  }
}
