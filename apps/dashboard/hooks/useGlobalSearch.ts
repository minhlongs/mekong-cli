'use client'

import { useState, useCallback, useEffect } from 'react'
import { logger } from '@/lib/utils/logger'
import { type SearchResult, SEARCH_INDEX, scoreResult } from './global-search-items'

export type { SearchResult }

const STORAGE_KEY = 'agencyos-recent-searches'

export function useGlobalSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [recentSearches, setRecentSearches] = useState<string[]>([])

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        setRecentSearches(JSON.parse(stored))
      }
    } catch (e) {
      logger.error('Failed to load recent searches', e)
    }
  }, [])

  const search = useCallback((q: string) => {
    setQuery(q)

    if (!q.trim()) {
      setResults([])
      return
    }

    const scored = SEARCH_INDEX.map(item => ({ item, score: scoreResult(q, item) }))
      .filter(({ score }) => score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10)
      .map(({ item }) => item)

    setResults(scored)
  }, [])

  const addToRecent = useCallback((term: string) => {
    if (!term.trim()) return

    setRecentSearches(prev => {
      const filtered = prev.filter(t => t !== term)
      const updated = [term, ...filtered].slice(0, 5)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      return updated
    })
  }, [])

  const clearRecent = useCallback(() => {
    setRecentSearches([])
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  const getSuggestions = useCallback(() => {
    return recentSearches.map(term => ({
      id: `recent-${term}`,
      title: term,
      subtitle: 'Recent search',
      category: 'recent' as const,
      icon: '🕐',
      keywords: [term],
    }))
  }, [recentSearches])

  return {
    query,
    search,
    results,
    recentSearches,
    addToRecent,
    clearRecent,
    getSuggestions,
    allContent: SEARCH_INDEX,
  }
}
