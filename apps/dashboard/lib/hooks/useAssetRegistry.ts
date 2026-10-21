'use client'

import { useState, useCallback, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import {
  type AssetType,
  type AssetStatus,
  type Asset,
  type AssetSummary,
  type UseAssetRegistryOptions,
  type AssetRow,
  mapAssetRow,
  computeAssetSummary,
  getDemoAssets,
} from './asset-registry-helpers'

export type { AssetType, AssetStatus, Asset, AssetSummary, UseAssetRegistryOptions }

/**
 * Asset Registry Hook
 * Track digital assets, licenses, subscriptions
 */
export function useAssetRegistry(options: UseAssetRegistryOptions = {}) {
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(false)
  const { autoFetch = true, onError } = options

  const fetchAssets = useCallback(async () => {
    setLoading(true)
    try {
      const supabase = createClient()
      const { data, error } = await supabase
        .from('assets')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) throw error
      setAssets((data || []).map((a: AssetRow) => mapAssetRow(a)))
    } catch {
      setAssets(getDemoAssets())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (autoFetch) {
      fetchAssets()
    }
  }, [autoFetch, fetchAssets])

  const summary: AssetSummary = computeAssetSummary(assets)

  const addAsset = useCallback(
    async (asset: Omit<Asset, 'id' | 'createdAt' | 'updatedAt'>) => {
      setLoading(true)
      try {
        const supabase = createClient()
        const now = new Date().toISOString()
        const { error } = await supabase
          .from('assets')
          .insert({ id: crypto.randomUUID(), ...asset, created_at: now, updated_at: now })
        if (error) throw error
        await fetchAssets()
      } catch (error) {
        onError?.(error as Error)
      } finally {
        setLoading(false)
      }
    },
    [fetchAssets, onError]
  )

  const updateAsset = useCallback(
    async (id: string, updates: Partial<Asset>) => {
      setLoading(true)
      try {
        const supabase = createClient()
        const { error } = await supabase
          .from('assets')
          .update({ ...updates, updated_at: new Date().toISOString() })
          .eq('id', id)

        if (error) throw error
        await fetchAssets()
      } catch (error) {
        onError?.(error as Error)
      } finally {
        setLoading(false)
      }
    },
    [fetchAssets, onError]
  )

  const deleteAsset = useCallback(
    async (id: string) => {
      setLoading(true)
      try {
        const supabase = createClient()
        const { error } = await supabase.from('assets').delete().eq('id', id)
        if (error) throw error
        await fetchAssets()
      } catch (error) {
        onError?.(error as Error)
      } finally {
        setLoading(false)
      }
    },
    [fetchAssets, onError]
  )

  const getExpiringAssets = useCallback(
    (days: number = 30) => {
      const cutoff = new Date()
      cutoff.setDate(cutoff.getDate() + days)
      return assets.filter(a => {
        if (!a.expiryDate) return false
        const expiry = new Date(a.expiryDate)
        return expiry <= cutoff && expiry >= new Date()
      })
    },
    [assets]
  )

  const getAssetsByType = useCallback(
    (type: AssetType) => assets.filter(a => a.type === type),
    [assets]
  )

  return {
    assets,
    summary,
    loading,
    fetchAssets,
    addAsset,
    updateAsset,
    deleteAsset,
    getExpiringAssets,
    getAssetsByType,
  }
}

export default useAssetRegistry
