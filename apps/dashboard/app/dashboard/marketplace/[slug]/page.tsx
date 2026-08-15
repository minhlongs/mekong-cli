'use client'

import React, { useState, useEffect, use } from 'react'
import { motion } from 'framer-motion'
import { Star, Download, ExternalLink, Terminal, ArrowLeft, Tag, Calendar, User, Box } from 'lucide-react'
import { AgencyCard } from '@/components/ui/agency-card'
import Link from 'next/link'

interface PluginDetail {
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
    short_description?: string
    author_id?: string
}

export default function PluginDetailPage({ params }: { params: Promise<{ slug: string }> }) {
    const { slug } = use(params)
    const [plugin, setPlugin] = useState<PluginDetail | null>(null)
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState<'description' | 'dependencies' | 'versions'>('description')

    useEffect(() => {
        const fetchPlugin = async () => {
            try {
                const response = await fetch(`/api/v1/marketplace/plugins/${slug}`)
                if (!response.ok) throw new Error('Plugin not found')
                const data = await response.json()
                setPlugin(data)
            } catch (error) {
                console.error('Error fetching plugin:', error)
                setPlugin(null)
            } finally {
                setLoading(false)
            }
        }
        fetchPlugin()
    }, [slug])

    const formatDownloads = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
        return num.toString()
    }

    const handleInstall = async () => {
        try {
            const response = await fetch('/api/v1/marketplace/plugins/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plugin_name: slug }),
            })
            if (response.ok) {
                alert(`To install ${plugin?.name}, run:\n\nmekong plugin install ${slug}\n\nOr copy this command to your terminal.`)
            } else {
                alert('Failed to get installation info')
            }
        } catch (error) {
            console.error('Install error:', error)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="text-neutral-400">Loading plugin details...</div>
            </div>
        )
    }

    if (!plugin) {
        return (
            <div className="flex flex-col items-center justify-center py-20">
                <p className="text-neutral-400 mb-4">Plugin not found</p>
                <Link href="/dashboard/marketplace" className="text-emerald-400 hover:underline">
                    Back to Marketplace
                </Link>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Breadcrumb */}
            <Link
                href="/dashboard/marketplace"
                className="inline-flex items-center gap-2 text-sm text-neutral-400 hover:text-emerald-400 transition-colors"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to Marketplace
            </Link>

            {/* Plugin Header */}
            <div className="flex flex-col md:flex-row gap-6 items-start">
                {/* Icon Placeholder */}
                <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/20 shrink-0">
                    <Box className="w-12 h-12 text-white" />
                </div>

                {/* Info */}
                <div className="flex-1 space-y-3">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <h1 className="text-2xl font-bold text-white">{plugin.name}</h1>
                            <p className="text-sm text-neutral-400">by {plugin.author} • v{plugin.version}</p>
                        </div>
                        {!plugin.is_free && plugin.price_cents && (
                            <span className="px-3 py-1.5 bg-emerald-500/20 text-emerald-400 text-sm font-medium rounded-full">
                                ${(plugin.price_cents / 100).toFixed(2)}
                            </span>
                        )}
                    </div>

                    <p className="text-neutral-300">{plugin.description}</p>

                    <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-400">
                        <div className="flex items-center gap-1">
                            <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                            <span className="font-medium text-white">{plugin.rating.toFixed(1)}</span>
                            <span className="text-neutral-500">({plugin.rating_count} reviews)</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <Download className="w-4 h-4" />
                            <span>{formatDownloads(plugin.downloads)} downloads</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <Box className="w-4 h-4" />
                            <span>{plugin.plugin_type}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            <span>Updated {plugin.updated_at ? new Date(plugin.updated_at).toLocaleDateString() : 'N/A'}</span>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {plugin.tags.map(tag => (
                            <span
                                key={tag}
                                className="px-2.5 py-1 bg-white/5 border border-white/10 text-neutral-300 text-xs rounded-full"
                            >
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
                <button
                    onClick={handleInstall}
                    className="flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl transition-colors shadow-lg shadow-emerald-500/20"
                >
                    <Terminal className="w-4 h-4" />
                    Install Plugin
                </button>
                {plugin.repository_url && (
                    <a
                        href={plugin.repository_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-colors"
                    >
                        <ExternalLink className="w-4 h-4" />
                        Repository
                    </a>
                )}
                {plugin.documentation_url && (
                    <a
                        href={plugin.documentation_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-colors"
                    >
                        Documentation
                    </a>
                )}
            </div>

            {/* Tabs */}
            <div className="border-b border-white/10">
                <div className="flex gap-6">
                    {(['description', 'dependencies', 'versions'] as const).map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`pb-3 px-1 text-sm font-medium transition-colors relative ${
                                activeTab === tab ? 'text-emerald-400' : 'text-neutral-400 hover:text-white'
                            }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            {activeTab === tab && (
                                <motion.div
                                    layoutId="tab-indicator"
                                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-400"
                                />
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Tab Content */}
            <AgencyCard variant="glass" className="p-6">
                {activeTab === 'description' && (
                    <div className="prose prose-invert max-w-none">
                        <p className="text-neutral-300 leading-relaxed whitespace-pre-line">
                            {plugin.description}
                        </p>
                    </div>
                )}

                {activeTab === 'dependencies' && (
                    <div className="space-y-4">
                        {plugin.dependencies.length === 0 ? (
                            <p className="text-neutral-400">No dependencies required.</p>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {plugin.dependencies.map(dep => (
                                    <div
                                        key={dep}
                                        className="flex items-center gap-3 p-3 bg-white/5 rounded-lg border border-white/5"
                                    >
                                        <div className="w-2 h-2 rounded-full bg-emerald-400" />
                                        <span className="text-neutral-200 font-mono text-sm">{dep}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                        <p className="text-xs text-neutral-500 mt-4">
                            Dependencies will be automatically installed when you install this plugin.
                        </p>
                    </div>
                )}

                {activeTab === 'versions' && (
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/5">
                            <div>
                                <p className="font-medium text-white">v{plugin.version}</p>
                                <p className="text-xs text-neutral-400">Current version</p>
                            </div>
                            <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded-full">
                                Latest
                            </span>
                        </div>
                        <p className="text-sm text-neutral-400">
                            Full version history available in the repository.
                        </p>
                    </div>
                )}
            </AgencyCard>

            {/* Additional Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <AgencyCard variant="glass" className="p-5">
                    <h3 className="font-bold text-white mb-3 flex items-center gap-2">
                        <User className="w-4 h-4" />
                        Developer
                    </h3>
                    <p className="text-neutral-300 text-sm">{plugin.author}</p>
                    {plugin.repository_url && (
                        <a
                            href={plugin.repository_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-emerald-400 text-sm mt-2 hover:underline"
                        >
                            View Repository <ExternalLink className="w-3 h-3" />
                        </a>
                    )}
                </AgencyCard>

                <AgencyCard variant="glass" className="p-5">
                    <h3 className="font-bold text-white mb-3 flex items-center gap-2">
                        <Tag className="w-4 h-4" />
                        Details
                    </h3>
                    <dl className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <dt className="text-neutral-400">License</dt>
                            <dd className="text-white">{plugin.license}</dd>
                        </div>
                        <div className="flex justify-between">
                            <dt className="text-neutral-400">Type</dt>
                            <dd className="text-white capitalize">{plugin.plugin_type}</dd>
                        </div>
                        <div className="flex justify-between">
                            <dt className="text-neutral-400">Min Mekong Version</dt>
                            <dd className="text-white">{plugin.min_mekong_version}</dd>
                        </div>
                    </dl>
                </AgencyCard>
            </div>
        </div>
    )
}
