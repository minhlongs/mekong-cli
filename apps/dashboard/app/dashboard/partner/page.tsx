'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
    Building2,
    TrendingUp,
    TrendingDown,
    AlertCircle,
    CheckCircle,
    Activity,
    CreditCard,
    Bell,
    Settings,
    Plus,
    ExternalLink
} from 'lucide-react'
import { AgencyCard } from '@/components/ui/agency-card'

interface PartnerCompany {
    id: string
    name: string
    health_score: number
    days_since_active: number
    credit_consumed: number
    credit_allocated: number
    onboarded: boolean
}

interface PortfolioSummary {
    total_companies: number
    active_companies: number
    avg_health_score: number
    total_credits_consumed: number
    total_credits_allocated: number
    alerts_count: number
}

interface Alert {
    id: string
    alert_type: string
    severity: 'info' | 'warning' | 'high' | 'critical'
    title: string
    description: string
    company_id?: string
    status: string
    created_at: string
}

export default function PartnerDashboardPage() {
    const [summary, setSummary] = useState<PortfolioSummary | null>(null)
    const [companies, setCompanies] = useState<PartnerCompany[]>([])
    const [alerts, setAlerts] = useState<Alert[]>([])
    const [loading, setLoading] = useState(true)
    const [healthDistribution, setHealthDistribution] = useState<{healthy: number; at_risk: number; critical: number; inactive: number}>({
        healthy: 0, at_risk: 0, critical: 0, inactive: 0
    })

    const fetchData = async () => {
        try {
            const [summaryRes, companiesRes, alertsRes, healthRes] = await Promise.all([
                fetch('/api/v1/partner/aggregate'),
                fetch('/api/v1/partner/portfolio'),
                fetch('/api/v1/partner/alerts?status_filter=open'),
                fetch('/api/v1/partner/health/portfolio')
            ])

            if (summaryRes.ok) setSummary(await summaryRes.json())
            if (companiesRes.ok) setCompanies(await companiesRes.json())
            if (alertsRes.ok) setAlerts(await alertsRes.json())
            if (healthRes.ok) {
                const healthData = await healthRes.json()
                setHealthDistribution(healthData.health_distribution || { healthy: 0, at_risk: 0, critical: 0, inactive: 0 })
            }
        } catch (error) {
            console.error('Error fetching partner data:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [])

    const handleAcknowledgeAlert = async (alertId: string) => {
        try {
            await fetch(`/api/v1/partner/alerts/${alertId}/acknowledge`, { method: 'POST' })
            setAlerts(alerts.filter(a => a.id !== alertId))
        } catch (error) {
            console.error('Error acknowledging alert:', error)
        }
    }

    const handleResolveAlert = async (alertId: string) => {
        try {
            await fetch(`/api/v1/partner/alerts/${alertId}/resolve`, { method: 'POST' })
            setAlerts(alerts.filter(a => a.id !== alertId))
        } catch (error) {
            console.error('Error resolving alert:', error)
        }
    }

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/30'
            case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
            case 'warning': return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
            default: return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
        }
    }

    const getHealthColor = (score: number) => {
        if (score >= 0.7) return 'text-emerald-400'
        if (score >= 0.4) return 'text-amber-400'
        return 'text-red-400'
    }

    const getHealthLabel = (score: number) => {
        if (score >= 0.7) return 'Healthy'
        if (score >= 0.4) return 'At Risk'
        return 'Critical'
    }

    const formatDate = (dateStr: string) => {
        try {
            return new Date(dateStr).toLocaleDateString()
        } catch {
            return 'N/A'
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-neutral-400">Loading partner dashboard...</div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-500/20 rounded-lg">
                        <Building2 className="w-6 h-6 text-emerald-400" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Partner Dashboard</h1>
                        <p className="text-neutral-400 text-sm">Monitor your portfolio companies and performance</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <a
                        href="/dashboard/partner/companies"
                        className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm transition-colors"
                    >
                        <Plus className="w-4 h-4" />
                        Add Company
                    </a>
                    <a
                        href="/dashboard/partner/settings"
                        className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm transition-colors"
                    >
                        <Settings className="w-4 h-4" />
                        Settings
                    </a>
                </div>
            </div>

            {/* Summary Cards */}
            {summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <AgencyCard variant="glass" className="p-4">
                        <div className="flex items-center gap-3 mb-2">
                            <Building2 className="w-5 h-5 text-emerald-400" />
                            <span className="text-sm text-neutral-400">Companies</span>
                        </div>
                        <p className="text-2xl font-bold text-white">{summary.total_companies}</p>
                        <p className="text-xs text-emerald-400">{summary.active_companies} active (7d)</p>
                    </AgencyCard>

                    <AgencyCard variant="glass" className="p-4">
                        <div className="flex items-center gap-3 mb-2">
                            <Activity className="w-5 h-5 text-blue-400" />
                            <span className="text-sm text-neutral-400">Health Score</span>
                        </div>
                        <p className={`text-2xl font-bold ${getHealthColor(summary.avg_health_score)}`}>
                            {(summary.avg_health_score * 100).toFixed(0)}%
                        </p>
                        <p className="text-xs text-neutral-400">Portfolio average</p>
                    </AgencyCard>

                    <AgencyCard variant="glass" className="p-4">
                        <div className="flex items-center gap-3 mb-2">
                            <CreditCard className="w-5 h-5 text-amber-400" />
                            <span className="text-sm text-neutral-400">Credits Used</span>
                        </div>
                        <p className="text-2xl font-bold text-white">
                            {summary.total_credits_consumed.toLocaleString()}
                        </p>
                        <p className="text-xs text-neutral-400">
                            of {summary.total_credits_allocated.toLocaleString()} allocated
                        </p>
                    </AgencyCard>

                    <AgencyCard variant="glass" className="p-4">
                        <div className="flex items-center gap-3 mb-2">
                            <Bell className="w-5 h-5 text-red-400" />
                            <span className="text-sm text-neutral-400">Open Alerts</span>
                        </div>
                        <p className="text-2xl font-bold text-white">{summary.alerts_count}</p>
                        <p className="text-xs text-neutral-400">Requires attention</p>
                    </AgencyCard>
                </div>
            )}

            {/* Health Distribution Chart */}
            <AgencyCard variant="glass" className="p-5">
                <h2 className="text-lg font-semibold text-white mb-4">Portfolio Health Distribution</h2>
                <div className="flex items-end gap-4 h-32">
                    {(['healthy', 'at_risk', 'critical', 'inactive'] as const).map((bucket) => {
                        const count = healthDistribution[bucket] || 0
                        const max = Math.max(...Object.values(healthDistribution), 1)
                        const height = (count / max) * 100
                        const colors: Record<string, string> = {
                            healthy: 'bg-emerald-500',
                            at_risk: 'bg-amber-500',
                            critical: 'bg-red-500',
                            inactive: 'bg-neutral-600'
                        }
                        return (
                            <div key={bucket} className="flex-1 flex flex-col items-center gap-2">
                                <div
                                    className="w-full rounded-t transition-all duration-300"
                                    style={{ height: `${height}%`, backgroundColor: colors[bucket] ? colors[bucket].replace('bg-', 'rgb-').replace('500', '500,0.8)') : '#666' }}
                                />
                                <span className="text-xs text-neutral-400 capitalize">{bucket.replace('_', ' ')}</span>
                                <span className="text-sm font-medium text-white">{count}</span>
                            </div>
                        )
                    })}
                </div>
            </AgencyCard>

            {/* Main Content Grid */}
            <div className="grid lg:grid-cols-2 gap-6">
                {/* Companies List */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-white">Portfolio Companies</h2>
                        <a href="/dashboard/partner/companies" className="text-sm text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
                            View all <ExternalLink className="w-3 h-3" />
                        </a>
                    </div>

                    {companies.length === 0 ? (
                        <AgencyCard variant="glass" className="p-8 text-center">
                            <Building2 className="w-12 h-12 text-neutral-600 mx-auto mb-3" />
                            <p className="text-neutral-400">No companies added yet</p>
                            <a
                                href="/dashboard/partner/companies"
                                className="inline-flex items-center gap-2 mt-3 px-4 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 rounded-lg text-sm transition-colors"
                            >
                                <Plus className="w-4 h-4" />
                                Add your first company
                            </a>
                        </AgencyCard>
                    ) : (
                        <div className="space-y-3">
                            {companies.slice(0, 5).map((company, idx) => (
                                <motion.div
                                    key={company.id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                >
                                    <AgencyCard variant="glass" className="p-4">
                                        <div className="flex items-center justify-between gap-4">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h3 className="font-medium text-white truncate">{company.name}</h3>
                                                    {!company.onboarded && (
                                                        <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded-full">
                                                            Pending
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-4 text-xs text-neutral-400">
                                                    <span className={`flex items-center gap-1 ${getHealthColor(company.health_score)}`}>
                                                        {company.health_score >= 0.5 ? (
                                                            <TrendingUp className="w-3 h-3" />
                                                        ) : (
                                                            <TrendingDown className="w-3 h-3" />
                                                        )}
                                                        {getHealthLabel(company.health_score)}
                                                    </span>
                                                    <span>{company.days_since_active}d inactive</span>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-sm font-medium text-white">
                                                    {company.credit_consumed} / {company.credit_allocated}
                                                </div>
                                                <div className="text-xs text-neutral-400">credits</div>
                                            </div>
                                        </div>
                                    </AgencyCard>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Alerts */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-white">Recent Alerts</h2>
                        <a href="/dashboard/partner/alerts" className="text-sm text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
                            View all <ExternalLink className="w-3 h-3" />
                        </a>
                    </div>

                    {alerts.length === 0 ? (
                        <AgencyCard variant="glass" className="p-8 text-center">
                            <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                            <p className="text-emerald-400 font-medium">All clear!</p>
                            <p className="text-neutral-400 text-sm">No active alerts</p>
                        </AgencyCard>
                    ) : (
                        <div className="space-y-3">
                            {alerts.slice(0, 5).map((alert, idx) => (
                                <motion.div
                                    key={alert.id}
                                    initial={{ opacity: 0, x: 10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                >
                                    <AgencyCard variant="glass" className={`p-4 border-l-4 ${getSeverityColor(alert.severity).split(' ')[2]}`}>
                                        <div className="flex items-start gap-3">
                                            <AlertCircle className={`w-5 h-5 flex-shrink-0 ${getSeverityColor(alert.severity).split(' ')[1]}`} />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h4 className="font-medium text-white text-sm">{alert.title}</h4>
                                                    <span className={`px-1.5 py-0.5 text-xs rounded ${getSeverityColor(alert.severity).split(' ').slice(0, 2).join(' ')}`}>
                                                        {alert.severity}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-neutral-400 mb-2">{alert.description}</p>
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        onClick={() => handleAcknowledgeAlert(alert.id)}
                                                        className="text-xs px-2 py-1 bg-white/10 hover:bg-white/20 text-white rounded transition-colors"
                                                    >
                                                        Acknowledge
                                                    </button>
                                                    <button
                                                        onClick={() => handleResolveAlert(alert.id)}
                                                        className="text-xs px-2 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded transition-colors"
                                                    >
                                                        Resolve
                                                    </button>
                                                    <span className="text-xs text-neutral-500">{formatDate(alert.created_at)}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </AgencyCard>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Quick Actions */}
            <AgencyCard variant="glass" className="p-5">
                <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <a
                        href="/dashboard/partner/companies/new"
                        className="flex items-center justify-center gap-2 p-4 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-emerald-400 transition-colors"
                    >
                        <Plus className="w-5 h-5" />
                        <span>Add Company</span>
                    </a>
                    <a
                        href="/dashboard/partner/analytics"
                        className="flex items-center justify-center gap-2 p-4 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-400 transition-colors"
                    >
                        <Activity className="w-5 h-5" />
                        <span>View Analytics</span>
                    </a>
                    <a
                        href="/dashboard/partner/webhooks"
                        className="flex items-center justify-center gap-2 p-4 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-lg text-purple-400 transition-colors"
                    >
                        <Bell className="w-5 h-5" />
                        <span>Configure Webhooks</span>
                    </a>
                    <a
                        href="/dashboard/partner/api-keys"
                        className="flex items-center justify-center gap-2 p-4 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded-lg text-amber-400 transition-colors"
                    >
                        <Settings className="w-5 h-5" />
                        <span>API Keys</span>
                    </a>
                </div>
            </AgencyCard>
        </div>
    )
}
