export type AssetType = 'software' | 'license' | 'subscription' | 'hardware' | 'domain' | 'other'
export type AssetStatus = 'active' | 'expiring' | 'expired' | 'disposed'

export interface Asset {
  id: string
  name: string
  type: AssetType
  status: AssetStatus
  vendor: string
  purchaseDate: string
  expiryDate?: string
  purchaseCost: number
  currentValue: number
  monthlyRecurring?: number
  assignedTo?: string
  notes?: string
  tags: string[]
  createdAt: string
  updatedAt: string
}

export interface AssetSummary {
  totalAssets: number
  totalValue: number
  monthlyRecurring: number
  expiringThisMonth: number
  byType: Record<AssetType, number>
  byStatus: Record<AssetStatus, number>
}

export interface UseAssetRegistryOptions {
  autoFetch?: boolean
  onError?: (error: Error) => void
}

export interface AssetRow {
  id: string
  name: string
  type: AssetType
  status: AssetStatus
  vendor: string
  purchase_date: string
  expiry_date?: string
  purchase_cost: number
  current_value: number
  monthly_recurring?: number
  assigned_to?: string
  notes?: string
  tags?: string[]
  created_at: string
  updated_at: string
}

export function mapAssetRow(a: AssetRow): Asset {
  return {
    id: a.id,
    name: a.name,
    type: a.type,
    status: a.status,
    vendor: a.vendor,
    purchaseDate: a.purchase_date,
    expiryDate: a.expiry_date,
    purchaseCost: a.purchase_cost,
    currentValue: a.current_value,
    monthlyRecurring: a.monthly_recurring,
    assignedTo: a.assigned_to,
    notes: a.notes,
    tags: a.tags || [],
    createdAt: a.created_at,
    updatedAt: a.updated_at,
  }
}

export function computeAssetSummary(assets: Asset[]): AssetSummary {
  return {
    totalAssets: assets.length,
    totalValue: assets.reduce((sum, a) => sum + a.currentValue, 0),
    monthlyRecurring: assets.reduce((sum, a) => sum + (a.monthlyRecurring || 0), 0),
    expiringThisMonth: assets.filter(a => {
      if (!a.expiryDate) return false
      const expiry = new Date(a.expiryDate)
      const now = new Date()
      return expiry.getMonth() === now.getMonth() && expiry.getFullYear() === now.getFullYear()
    }).length,
    byType: assets.reduce(
      (acc, a) => {
        acc[a.type] = (acc[a.type] || 0) + 1
        return acc
      },
      {} as Record<AssetType, number>
    ),
    byStatus: assets.reduce(
      (acc, a) => {
        acc[a.status] = (acc[a.status] || 0) + 1
        return acc
      },
      {} as Record<AssetStatus, number>
    ),
  }
}

export function getDemoAssets(): Asset[] {
  return [
    {
      id: '1',
      name: 'Figma Enterprise',
      type: 'subscription',
      status: 'active',
      vendor: 'Figma',
      purchaseDate: '2025-01-01',
      expiryDate: '2026-01-01',
      purchaseCost: 0,
      currentValue: 0,
      monthlyRecurring: 75,
      assignedTo: 'Design Team',
      notes: 'Enterprise plan with Dev Mode',
      tags: ['design', 'collaboration'],
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    {
      id: '2',
      name: 'Vercel Pro',
      type: 'subscription',
      status: 'active',
      vendor: 'Vercel',
      purchaseDate: '2025-01-01',
      expiryDate: '2026-01-01',
      purchaseCost: 0,
      currentValue: 0,
      monthlyRecurring: 20,
      assignedTo: 'Dev Team',
      notes: 'Hosting for frontend apps',
      tags: ['hosting', 'dev'],
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    {
      id: '3',
      name: 'agencyos.network',
      type: 'domain',
      status: 'active',
      vendor: 'Cloudflare',
      purchaseDate: '2024-06-15',
      expiryDate: '2025-06-15',
      purchaseCost: 15,
      currentValue: 15,
      tags: ['domain', 'primary'],
      createdAt: '2024-06-15T00:00:00Z',
      updatedAt: '2024-06-15T00:00:00Z',
    },
    {
      id: '4',
      name: 'Adobe Creative Cloud',
      type: 'license',
      status: 'expiring',
      vendor: 'Adobe',
      purchaseDate: '2024-02-01',
      expiryDate: '2026-02-01',
      purchaseCost: 600,
      currentValue: 300,
      monthlyRecurring: 55,
      assignedTo: 'Creative Team',
      tags: ['design', 'video'],
      createdAt: '2024-02-01T00:00:00Z',
      updatedAt: '2024-02-01T00:00:00Z',
    },
  ]
}
