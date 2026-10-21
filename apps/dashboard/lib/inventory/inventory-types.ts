/**
 * Inventory & Asset Management Types and Mappers for AgencyOS
 * ERPNext Parity: Asset Registry, Stock Ledger, License Tracking
 */

export type AssetType =
  | 'hardware' // Physical equipment
  | 'software' // Software licenses
  | 'subscription' // SaaS subscriptions
  | 'digital' // Digital assets (domains, etc.)
  | 'other'

export type AssetStatus = 'active' | 'in_use' | 'maintenance' | 'retired' | 'disposed'

export interface Asset {
  id: string
  tenantId: string
  name: string
  type: AssetType
  category: string
  code: string
  serialNumber?: string
  purchaseDate?: Date
  purchasePrice?: number
  currentValue?: number
  depreciationRate?: number
  vendor?: string
  assignedTo?: string
  status: AssetStatus
  location?: string
  notes?: string
  expiryDate?: Date
  renewalDate?: Date
  metadata?: Record<string, unknown>
  createdAt: Date
  updatedAt: Date
}

export interface AssetMovement {
  id: string
  assetId: string
  fromLocation?: string
  toLocation?: string
  fromAssignee?: string
  toAssignee?: string
  movementType: 'assignment' | 'transfer' | 'return' | 'maintenance' | 'disposal'
  date: Date
  notes?: string
  performedBy: string
  createdAt: Date
}

export interface LicenseInfo {
  id: string
  tenantId: string
  assetId?: string
  name: string
  vendor: string
  licenseKey?: string
  seats: number
  usedSeats: number
  purchaseDate: Date
  expiryDate?: Date
  cost: number
  billingCycle: 'monthly' | 'yearly' | 'perpetual'
  status: 'active' | 'expired' | 'cancelled'
  createdAt: Date
}

export interface AssetSummary {
  totalAssets: number
  byType: Record<AssetType, number>
  byStatus: Record<AssetStatus, number>
  totalValue: number
  expiringThisMonth: number
}

export interface AssetRow {
  id: string
  tenant_id: string
  name: string
  type: AssetType
  category: string
  code: string
  serial_number?: string
  purchase_date?: string
  purchase_price?: number
  current_value?: number
  depreciation_rate?: number
  vendor?: string
  assigned_to?: string
  status: AssetStatus
  location?: string
  notes?: string
  expiry_date?: string
  renewal_date?: string
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export function mapAssetToDb(asset: Partial<Asset>): Record<string, unknown> {
  return {
    name: asset.name,
    type: asset.type,
    category: asset.category,
    serial_number: asset.serialNumber,
    purchase_date: asset.purchaseDate?.toISOString(),
    purchase_price: asset.purchasePrice,
    current_value: asset.currentValue,
    depreciation_rate: asset.depreciationRate,
    vendor: asset.vendor,
    assigned_to: asset.assignedTo,
    status: asset.status,
    location: asset.location,
    notes: asset.notes,
    expiry_date: asset.expiryDate?.toISOString(),
    renewal_date: asset.renewalDate?.toISOString(),
    metadata: asset.metadata,
  }
}

export function mapAssetFromDb(data: AssetRow): Asset {
  return {
    id: data.id,
    tenantId: data.tenant_id,
    name: data.name,
    type: data.type,
    category: data.category,
    code: data.code,
    serialNumber: data.serial_number,
    purchaseDate: data.purchase_date ? new Date(data.purchase_date) : undefined,
    purchasePrice: data.purchase_price,
    currentValue: data.current_value,
    depreciationRate: data.depreciation_rate,
    vendor: data.vendor,
    assignedTo: data.assigned_to,
    status: data.status,
    location: data.location,
    notes: data.notes,
    expiryDate: data.expiry_date ? new Date(data.expiry_date) : undefined,
    renewalDate: data.renewal_date ? new Date(data.renewal_date) : undefined,
    metadata: data.metadata,
    createdAt: new Date(data.created_at),
    updatedAt: new Date(data.updated_at),
  }
}
