'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { RefreshCw, Trash2, Power, PowerOff, Terminal, AlertCircle } from 'lucide-react'
import { AgencyCard } from '@/components/ui/agency-card'

interface InstalledPlugin {
    name: string
    version: string
    plugin_type: string
    description: string
    author: string
    source: string
    status: string
    installed_at: string
    error_message: string | null
}

export default function MyPluginsPage() {
    const [plugins, setPlugins] = useState<InstalledPlugin[]>([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [actionLoading, setActionLoading] = useState<string | null>(null)

    const fetchPlugins = async () => {
        try {
            const response = await fetch('/api/v1/plugins')
            if (!response.ok) throw new Error('Failed to fetch plugins')
            const data = await response.json()
            setPlugins(data.plugins || [])
        } catch (error) {
            console.error('Error fetching plugins:', error)
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    useEffect(() => {
        fetchPlugins()
    }, [])

    const handleRefresh = () => {
        setRefreshing(true)
        fetchPlugins()
    }

    const handleAction = async (pluginName: string, action: 'activate' | 'deactivate' | 'uninstall') => {
        if (!confirm(`Are you sure you want to ${action} plugin "${pluginName}"?`)) {
            return
        }

        setActionLoading(pluginName)
        try {
            const endpoint = `/api/v1/plugins/${pluginName}/${action}`
            const response = await fetch(endpoint, { method: action === 'uninstall' ? 'DELETE' : 'POST' })
            if (!response.ok) {
                const err = await response.json().catch(() => ({}))
                throw new Error(err.detail || `Failed to ${action} plugin`)
            }
            await fetchPlugins() // Refresh list
        } catch (error) {
            console.error(`Error ${action}ing plugin:`, error)
            alert(`Failed to ${action} plugin: ${error instanceof Error ? error.message : 'Unknown error'}`)
        } finally {
            setActionLoading(null)
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-emerald-500/20 text-emerald-400'
            case 'installed': return 'bg-blue-500/20 text-blue-400'
            case 'disabled': return 'bg-neutral-500/20 text-neutral-400'
            case 'error': return 'bg-red-500/20 text-red-400'
            default: return 'bg-neutral-500/20 text-neutral-400'
        }
    }

    const formatDate = (dateStr: string) => {
        try {
            return new Date(dateStr).toLocaleDateString()
        } catch {
            return 'N/A'
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">My Plugins</h1>
                    <p className="text-neutral-400 text-sm mt-1">
                        Manage your installed Mekong CLI plugins
                    </p>
                </div>
                <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                    <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>

            {/* Plugin List */}
            {loading ? (
                <div className="text-center py-12 text-neutral-400">Loading plugins...</div>
            ) : plugins.length === 0 ? (
                <AgencyCard variant="glass" className="p-8 text-center">
                    <div className="flex flex-col items-center gap-3">
                        <Terminal className="w-12 h-12 text-neutral-500" />
                        <p className="text-neutral-300 font-medium">No plugins installed</p>
                        <p className="text-neutral-400 text-sm">Visit the marketplace to discover and install plugins</p>
                        <a
                            href="/dashboard/marketplace"
                            className="mt-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                            Browse Marketplace
                        </a>
                    </div>
                </AgencyCard>
            ) : (
                <div className="space-y-4">
                    {plugins.map((plugin, idx) => (
                        <motion.div
                            key={plugin.name}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.05 }}
                        >
                            <AgencyCard variant="glass" className="p-5">
                                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                                    {/* Plugin Info */}
                                    <div className="flex-1 space-y-2">
                                        <div className="flex items-center gap-3">
                                            <h3 className="font-bold text-white text-lg">{plugin.name}</h3>
                                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getStatusColor(plugin.status)}`}>
                                                {plugin.status}
                                            </span>
                                        </div>
                                        <p className="text-sm text-neutral-300 line-clamp-2">{plugin.description}</p>
                                        <div className="flex flex-wrap items-center gap-4 text-xs text-neutral-400">
                                            <span>v{plugin.version}</span>
                                            <span>•</span>
                                            <span>{plugin.author}</span>
                                            <span>•</span>
                                            <span>Installed {formatDate(plugin.installed_at)}</span>
                                            {plugin.error_message && (
                                                <>
                                                    <span>•</span>
                                                    <span className="text-red-400 flex items-center gap-1">
                                                        <AlertCircle className="w-3 h-3" />
                                                        Error
                                                    </span>
                                                </>
                                            )}
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center gap-2 mt-3 md:mt-0">
                                        {plugin.status === 'active' ? (
                                            <button
                                                onClick={() => handleAction(plugin.name, 'deactivate')}
                                                disabled={actionLoading === plugin.name}
                                                className="flex items-center gap-2 px-4 py-2 bg-neutral-700 hover:bg-neutral-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                                title="Deactivate plugin"
                                            >
                                                <PowerOff className="w-4 h-4" />
                                                Deactivate
                                            </button>
                                        ) : (
                                            plugin.status === 'installed' && (
                                                <button
                                                    onClick={() => handleAction(plugin.name, 'activate')}
                                                    disabled={actionLoading === plugin.name}
                                                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                                    title="Activate plugin"
                                                >
                                                    <Power className="w-4 h-4" />
                                                    Activate
                                                </button>
                                            )
                                        )}

                                        <button
                                            onClick={() => handleAction(plugin.name, 'uninstall')}
                                            disabled={actionLoading === plugin.name}
                                            className="flex items-center gap-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                            title="Uninstall plugin"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                            Uninstall
                                        </button>
                                    </div>
                                </div>

                                {/* Error message display */}
                                {plugin.error_message && (
                                    <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                                        <p className="text-red-400 text-sm">
                                            <strong>Error:</strong> {plugin.error_message}
                                        </p>
                                    </div>
                                )}
                            </AgencyCard>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Info Banner */}
            <AgencyCard variant="glass" className="p-4">
                <div className="flex items-start gap-3">
                    <Terminal className="w-5 h-5 text-emerald-400 mt-0.5" />
                    <div className="text-sm text-neutral-300">
                        <p className="font-medium text-white mb-1">Command Line Alternative</p>
                        <p className="text-neutral-400">
                            You can also manage plugins via the CLI:{' '}
                            <code className="px-1.5 py-0.5 bg-white/5 rounded text-emerald-300 font-mono text-xs">
                                mekong plugin list
                            </code>
                            {' '}to list, and{' '}
                            <code className="px-1.5 py-0.5 bg-white/5 rounded text-emerald-300 font-mono text-xs">
                                mekong plugin uninstall &lt;name&gt;
                            </code>{' '}
                            to remove.
                        </p>
                    </div>
                </div>
            </AgencyCard>
        </div>
    )
}
