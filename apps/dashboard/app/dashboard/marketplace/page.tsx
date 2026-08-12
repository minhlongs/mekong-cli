'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search, Star, Download, Filter, ExternalLink, Terminal } from 'lucide-react'
import { AgencyCard } from '@/components/ui/agency-card'

interface Plugin {
    name: string
    version: string
    description: string
    author: string
    plugin_type: string
    downloads: number
    rating: number
    rating_count: number
    tags: string[]
    repository_url?: string
    documentation_url?: string
    created_at?: string
    updated_at?: string
    license: string
    min_mekong_version: string
    dependencies: string[]
    is_free: boolean
    price_cents?: number
}

export default function MarketplacePage() {
    const [plugins, setPlugins] = useState<Plugin[]>([])
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedCategory, setSelectedCategory] = useState<string>('all')
    const [selectedType, setSelectedType] = useState<string>('all')
    const [showFreeOnly, setShowFreeOnly] = useState(false)
    const [loading, setLoading] = useState(true)

    // Fetch plugins from API
    const fetchPlugins = async () => {
        setLoading(true)
        try {
            const params = new URLSearchParams()
            if (searchQuery) params.append('q', searchQuery)
            if (selectedCategory !== 'all') params.append('category', selectedCategory)
            if (selectedType !== 'all') params.append('plugin_type', selectedType)
            if (showFreeOnly) params.append('is_free', 'true')

            const response = await fetch(`/api/v1/marketplace/plugins?${params.toString()}`)
            if (!response.ok) throw new Error('Failed to fetch plugins')
            const data = await response.json()
            setPlugins(data.plugins || [])
        } catch (error) {
            console.error('Error fetching plugins:', error)
            setPlugins([])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchPlugins()
    }, [searchQuery, selectedCategory, selectedType, showFreeOnly])

    const categories = [
        { id: 'all', name: 'All Categories' },
        { id: 'engineering', name: 'Engineering' },
        { id: 'business', name: 'Business' },
        { id: 'marketing', name: 'Marketing' },
        { id: 'productivity', name: 'Productivity' },
        { id: 'finance', name: 'Finance' },
    ]

    const pluginTypes = [
        { id: 'all', name: 'All Types' },
        { id: 'agent', name: 'Agent' },
        { id: 'provider', name: 'Provider' },
        { id: 'hook', name: 'Hook' },
        { id: 'recipe', name: 'Recipe' },
    ]

    const formatDownloads = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
        return num.toString()
    }

    const handleInstall = async (pluginName: string) => {
        try {
            const response = await fetch('/api/v1/marketplace/plugins/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plugin_name: pluginName }),
            })
            if (response.ok) {
                const data = await response.json()
                alert(`Installation command: mekong plugin install ${pluginName}\n\nOr use the CLI to complete installation.`)
            } else {
                alert('Failed to get installation info')
            }
        } catch (error) {
            console.error('Install error:', error)
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Plugin Marketplace</h1>
                    <p className="text-neutral-400 text-sm mt-1">
                        Discover and extend Mekong CLI with community plugins
                    </p>
                </div>
            </div>

            {/* Search and Filters */}
            <div className="flex flex-col md:flex-row gap-4">
                {/* Search */}
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                    <input
                        type="text"
                        placeholder="Search plugins by name, description, or tag..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                    />
                </div>

                {/* Filters */}
                <div className="flex gap-3">
                    <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                    >
                        {categories.map(cat => (
                            <option key={cat.id} value={cat.id}>{cat.name}</option>
                        ))}
                    </select>

                    <select
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value)}
                        className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                    >
                        {pluginTypes.map(type => (
                            <option key={type.id} value={type.id}>{type.name}</option>
                        ))}
                    </select>

                    <label className="flex items-center gap-2 px-4 py-3 bg-white/5 border border-white/10 rounded-xl cursor-pointer">
                        <input
                            type="checkbox"
                            checked={showFreeOnly}
                            onChange={(e) => setShowFreeOnly(e.target.checked)}
                            className="rounded text-emerald-600"
                        />
                        <span className="text-sm text-white">Free only</span>
                    </label>
                </div>
            </div>

            {/* Plugin Grid */}
            {loading ? (
                <div className="text-center py-12 text-neutral-400">Loading plugins...</div>
            ) : plugins.length === 0 ? (
                <div className="text-center py-12 text-neutral-400">
                    No plugins found matching your criteria.
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {plugins.map((plugin, idx) => (
                        <motion.div
                            key={plugin.name}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.05 }}
                        >
                            <AgencyCard variant="glass" className="h-full flex flex-col p-5">
                                <div className="flex-1 space-y-3">
                                    {/* Header */}
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <h3 className="font-bold text-white text-lg">{plugin.name}</h3>
                                            <p className="text-xs text-neutral-400">v{plugin.version} • {plugin.author}</p>
                                        </div>
                                        {!plugin.is_free && plugin.price_cents && (
                                            <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded-full">
                                                ${(plugin.price_cents / 100).toFixed(2)}
                                            </span>
                                        )}
                                    </div>

                                    {/* Description */}
                                    <p className="text-sm text-neutral-300 line-clamp-3">{plugin.description}</p>

                                    {/* Metadata */}
                                    <div className="flex items-center gap-4 text-xs text-neutral-400">
                                        <div className="flex items-center gap-1">
                                            <Star className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />
                                            <span>{plugin.rating.toFixed(1)}</span>
                                            <span className="text-neutral-500">({plugin.rating_count})</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <Download className="w-3.5 h-3.5" />
                                            <span>{formatDownloads(plugin.downloads)}</span>
                                        </div>
                                    </div>

                                    {/* Tags */}
                                    <div className="flex flex-wrap gap-2">
                                        {plugin.tags.slice(0, 4).map(tag => (
                                            <span
                                                key={tag}
                                                className="px-2 py-1 bg-white/5 text-neutral-300 text-xs rounded"
                                            >
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex gap-2 mt-4 pt-4 border-t border-white/5">
                                    <button
                                        onClick={() => handleInstall(plugin.name)}
                                        className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                                    >
                                        <Terminal className="w-4 h-4" />
                                        Install
                                    </button>
                                    {plugin.documentation_url && (
                                        <a
                                            href={plugin.documentation_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
                                        >
                                            <ExternalLink className="w-4 h-4" />
                                            Docs
                                        </a>
                                    )}
                                </div>
                            </AgencyCard>
                        </motion.div>
                    ))}
                </div>
            )}
        </div>
    )
}
