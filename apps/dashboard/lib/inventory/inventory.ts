/**
 * Inventory & Asset Management Module for AgencyOS
 * ERPNext Parity: Asset Registry, Stock Ledger, License Tracking
 */

import { createClient } from '@supabase/supabase-js'
import type {
  Asset,
  AssetMovement,
  AssetRow,
  AssetStatus,
  AssetSummary,
  AssetType,
  LicenseInfo,
} from './inventory-types'
import { mapAssetFromDb, mapAssetToDb } from './inventory-types'
import {
  type RecordAssetMovementInput,
  getAssetHistoryWithClient,
  recordAssetMovementWithClient,
} from './inventory-movements'
import {
  computeAssetSummary,
  createLicenseWithClient,
  listLicensesWithClient,
} from './inventory-valuation'

export * from './inventory-types'
export * from './inventory-seed'
export * from './inventory-movements'
export * from './inventory-valuation'

export class InventoryService {
  private supabase

  constructor() {
    this.supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    )
  }

  async createAsset(
    tenantId: string,
    asset: Omit<Asset, 'id' | 'tenantId' | 'createdAt' | 'updatedAt'>
  ): Promise<Asset> {
    const code = await this.generateAssetCode(tenantId, asset.type)
    const { data, error } = await this.supabase
      .from('assets')
      .insert({ tenant_id: tenantId, ...this.mapToDb(asset), code })
      .select()
      .single()

    if (error) throw new Error(`Failed to create asset: ${error.message}`)
    return this.mapFromDb(data)
  }

  async getAsset(tenantId: string, assetId: string): Promise<Asset | null> {
    const { data } = await this.supabase
      .from('assets')
      .select('*')
      .eq('tenant_id', tenantId)
      .eq('id', assetId)
      .single()
    return data ? this.mapFromDb(data) : null
  }

  async listAssets(
    tenantId: string,
    filters?: {
      type?: AssetType
      status?: AssetStatus
      assignedTo?: string
      expiringWithinDays?: number
    }
  ): Promise<Asset[]> {
    let query = this.supabase
      .from('assets')
      .select('*')
      .eq('tenant_id', tenantId)
      .order('created_at', { ascending: false })

    if (filters?.type) query = query.eq('type', filters.type)
    if (filters?.status) query = query.eq('status', filters.status)
    if (filters?.assignedTo) query = query.eq('assigned_to', filters.assignedTo)
    if (filters?.expiringWithinDays) {
      const futureDate = new Date()
      futureDate.setDate(futureDate.getDate() + filters.expiringWithinDays)
      query = query.lte('expiry_date', futureDate.toISOString())
    }

    const { data, error } = await query
    if (error) throw new Error(`Failed to list assets: ${error.message}`)
    return (data || []).map(this.mapFromDb)
  }

  async updateAsset(tenantId: string, assetId: string, updates: Partial<Asset>): Promise<Asset> {
    const { data, error } = await this.supabase
      .from('assets')
      .update(this.mapToDb(updates))
      .eq('tenant_id', tenantId)
      .eq('id', assetId)
      .select()
      .single()
    if (error) throw new Error(`Failed to update asset: ${error.message}`)
    return this.mapFromDb(data)
  }

  async deleteAsset(tenantId: string, assetId: string): Promise<void> {
    const { error } = await this.supabase.from('assets').delete().eq('tenant_id', tenantId).eq('id', assetId)
    if (error) throw new Error(`Failed to delete asset: ${error.message}`)
  }

  async recordMovement(
    tenantId: string,
    assetId: string,
    movement: RecordAssetMovementInput,
    performedBy: string
  ): Promise<AssetMovement> {
    const asset = await this.getAsset(tenantId, assetId)
    if (!asset) throw new Error('Asset not found')

    const recorded = await recordAssetMovementWithClient(this.supabase, asset, movement, performedBy)
    await this.updateAsset(tenantId, assetId, {
      location: movement.toLocation || asset.location,
      assignedTo: movement.toAssignee || asset.assignedTo,
    })
    return recorded
  }

  async getAssetHistory(_tenantId: string, assetId: string): Promise<AssetMovement[]> {
    return getAssetHistoryWithClient(this.supabase, assetId)
  }

  async createLicense(
    tenantId: string,
    license: Omit<LicenseInfo, 'id' | 'tenantId' | 'createdAt'>
  ): Promise<LicenseInfo> {
    return createLicenseWithClient(this.supabase, tenantId, license)
  }

  async listLicenses(tenantId: string): Promise<LicenseInfo[]> {
    return listLicensesWithClient(this.supabase, tenantId)
  }

  async getAssetSummary(tenantId: string): Promise<AssetSummary> {
    return computeAssetSummary(await this.listAssets(tenantId))
  }

  private async generateAssetCode(tenantId: string, type: AssetType): Promise<string> {
    const prefix = type.toUpperCase().substring(0, 3)
    const { count } = await this.supabase
      .from('assets')
      .select('*', { count: 'exact', head: true })
      .eq('tenant_id', tenantId)
      .eq('type', type)
    return `${prefix}-${String((count || 0) + 1).padStart(5, '0')}`
  }

  private mapToDb(asset: Partial<Asset>): Record<string, unknown> {
    return mapAssetToDb(asset)
  }
  private mapFromDb(data: AssetRow): Asset {
    return mapAssetFromDb(data)
  }
}

export function getInventoryService() {
  return new InventoryService()
}
