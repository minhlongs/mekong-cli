/**
 * Inventory Asset Movements & Ledger Operations
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { Asset, AssetMovement } from './inventory-types'

export interface RecordAssetMovementInput {
  movementType: AssetMovement['movementType']
  toLocation?: string
  toAssignee?: string
  notes?: string
}

export async function recordAssetMovementWithClient(
  supabase: SupabaseClient,
  asset: Asset,
  movement: RecordAssetMovementInput,
  performedBy: string
): Promise<AssetMovement> {
  const { data, error } = await supabase
    .from('asset_movements')
    .insert({
      asset_id: asset.id,
      from_location: asset.location,
      to_location: movement.toLocation,
      from_assignee: asset.assignedTo,
      to_assignee: movement.toAssignee,
      movement_type: movement.movementType,
      date: new Date().toISOString(),
      notes: movement.notes,
      performed_by: performedBy,
    })
    .select()
    .single()

  if (error) throw new Error(`Failed to record movement: ${error.message}`)

  return {
    id: data.id,
    assetId: data.asset_id,
    fromLocation: data.from_location,
    toLocation: data.to_location,
    fromAssignee: data.from_assignee,
    toAssignee: data.to_assignee,
    movementType: data.movement_type,
    date: new Date(data.date),
    notes: data.notes,
    performedBy: data.performed_by,
    createdAt: new Date(data.created_at),
  }
}

export async function getAssetHistoryWithClient(
  supabase: SupabaseClient,
  assetId: string
): Promise<AssetMovement[]> {
  const { data, error } = await supabase
    .from('asset_movements')
    .select('*')
    .eq('asset_id', assetId)
    .order('date', { ascending: false })

  if (error) throw new Error(`Failed to get asset history: ${error.message}`)

  return (data || []).map(m => ({
    id: m.id,
    assetId: m.asset_id,
    fromLocation: m.from_location,
    toLocation: m.to_location,
    fromAssignee: m.from_assignee,
    toAssignee: m.to_assignee,
    movementType: m.movement_type,
    date: new Date(m.date),
    notes: m.notes,
    performedBy: m.performed_by,
    createdAt: new Date(m.created_at),
  }))
}
