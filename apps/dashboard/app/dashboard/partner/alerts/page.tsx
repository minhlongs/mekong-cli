'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Bell, AlertCircle, CheckCircle, XCircle, Clock } from 'lucide-react'
import { AgencyCard } from '@/components/ui/agency-card'

interface Alert {
    id: string
    alert_type: string
    severity: 'info' | 'warning' | 'high' | 'critical'
    title: string
    description: string
    company_id?: string
    company_name?: string
    status: 'open' | 'acknowledged' | 'resolved' | 'dismissed'
    created_at: string
    acknowledged_by?: string
    acknowledged_at?: string
    resolved_at?: string
    resolution_notes?: string
}

export default function PartnerAlertsPage() {
    const [alerts, setAlerts] = useState<Alert[]>([])
    const [filter, setFilter] = useState<'open' | 'acknowledged' | 'resolved'>('open')
    const [loading, setLoading] = useState(true)

    const fetchAlerts = async () => {
        try {
            const response = await fetch(`/api/v1/partner/alerts?status_filter=${filter}`)
            if (response.ok) {
                setAlerts(await response.json())
            }
        } catch (error) {
            console.error('Error fetching alerts:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchAlerts()
    }, [filter])

    const handleAcknowledge = async (alertId: string) => {
        try {
            const response = await fetch(`/api/v1/partner/alerts/${alertId}/acknowledge`, { method: 'POST' })
            if (response.ok) {
                fetchAlerts()
            }
        } catch (error) {
            console.error('Error acknowledging alert:', error)
        }
    }

    const handleResolve = async (alertId: string, notes?: string) => {
        try {
            const response = await fetch(`/api/v1/partner/alerts/${alertId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ resolution_notes: notes })
            })
            if (response.ok) {
                fetchAlerts()
            }
        } catch (error) {
            console.error('Error resolving alert:', error)
        }
    }

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'critical': return {
                bg: 'bg-red-500/10',
                border: 'border-red-500/30',
                text: 'text-red-400',
                badge: 'bg-red-500/20 text-red-400'
            }
            case 'high': return {
                bg: 'bg-orange-500/10',
                border: 'border-orange-500/30',
                text: 'text-orange-400',
                badge: 'bg-orange-500/20 text-orange-400'
            }
            case 'warning': return {
                bg: 'bg-amber-500/10',
                border: 'border-amber-500/30',
                text: 'text-amber-400',
                badge: 'bg-amber-500/20 text-amber-400'
            }
            default: return {
                bg: 'bg-blue-500/10',
                border: 'border-blue-500/30',
                text: 'text-blue-400',
                badge: 'bg-blue-500/20 text-blue-400'
            }
        }
    }

    const getAlertTypeIcon = (type: string) => {
        switch (type) {
            case 'low_credits': return <Bell className="w-5 h-5" />
            case 'health_score_drop': return <AlertCircle className="w-5 h-5" />
            case 'inactive_company': return <Clock className="w-5 h-5" />
            case 'spike_detected': return <Bell className="w-5 h-5" />
            default: return <AlertCircle className="w-5 h-5" />
        }
    }

    const formatDate = (dateStr: string) => {
        try {
            const date = new Date(dateStr)
            const now = new Date()
            const diffMs = now.getTime() - date.getTime()
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
            const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

            if (diffHours < 1) return 'Just now'
            if (diffHours < 24) return `${diffHours}h ago`
            if (diffDays < 7) return `${diffDays}d ago`
            return date.toLocaleDateString()
        } catch {
            return 'N/A'
        }
    }

    const getFilterBadgeColor = (status: string) => {
        switch (status) {
            case 'open': return 'bg-red-500/20 text-red-400'
            case 'acknowledged': return 'bg-amber-500/20 text-amber-400'
            case 'resolved': return 'bg-emerald-500/20 text-emerald-400'
            default: return 'bg-neutral-500/20 text-neutral-400'
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-neutral-400">Loading alerts...</div>
            </div>
        )
    }

    // Group alerts by severity
    const groupedAlerts = alerts.reduce((acc, alert) => {
        const severity = alert.severity
        if (!acc[severity]) acc[severity] = []
        acc[severity].push(alert)
        return acc
    }, {} as Record<string, Alert[]>)

    const severityOrder = ['critical', 'high', 'warning', 'info']
    const sortedSeverities = Object.keys(groupedAlerts).sort((a, b) =>
        severityOrder.indexOf(a) - severityOrder.indexOf(b)
    )

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Alerts</h1>
                    <p className="text-neutral-400 text-sm mt-1">
                        Monitor and respond to portfolio notifications
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    {['open', 'acknowledged', 'resolved'].map((status) => (
                        <button
                            key={status}
                            onClick={() => setFilter(status as any)}
                            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                                filter === status
                                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                    : 'bg-white/5 text-neutral-400 hover:bg-white/10'
                            }`}
                        >
                            {status.charAt(0).toUpperCase() + status.slice(1)}
                            {status === 'open' && alerts.filter(a => a.status === 'open').length > 0 && (
                                <span className="ml-2 px-1.5 py-0.5 bg-red-500 text-white rounded-full text-xs">
                                    {alerts.filter(a => a.status === 'open').length}
                                </span>
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Alerts List */}
            {alerts.length === 0 ? (
                <AgencyCard variant="glass" className="p-12 text-center">
                    <CheckCircle className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
                    <p className="text-emerald-400 font-medium text-lg">All clear!</p>
                    <p className="text-neutral-400 mt-1">
                        {filter === 'open'
                            ? 'No open alerts requiring attention'
                            : `No ${filter} alerts`}
                    </p>
                </AgencyCard>
            ) : (
                <div className="space-y-6">
                    {sortedSeverities.map((severity) => (
                        <div key={severity} className="space-y-3">
                            <h2 className="text-sm font-medium text-neutral-400 uppercase tracking-wider">
                                {severity} ({groupedAlerts[severity].length})
                            </h2>
                            {groupedAlerts[severity].map((alert, idx) => {
                                const colors = getSeverityColor(alert.severity)
                                const isOpen = alert.status === 'open'

                                return (
                                    <motion.div
                                        key={alert.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                    >
                                        <AgencyCard variant="glass" className={`p-4 ${colors.border} border-l-4`}>
                                            <div className="flex items-start gap-4">
                                                <div className={`p-2 rounded-lg ${colors.bg}`}>
                                                    {getAlertTypeIcon(alert.alert_type)}
                                                </div>

                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <h3 className="font-semibold text-white">{alert.title}</h3>
                                                        <span className={`px-1.5 py-0.5 text-xs rounded ${colors.badge}`}>
                                                            {alert.severity}
                                                        </span>
                                                        <span className={`px-1.5 py-0.5 text-xs rounded ${getFilterBadgeColor(alert.status)}`}>
                                                            {alert.status}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-neutral-300 mb-2">{alert.description}</p>

                                                    <div className="flex flex-wrap items-center gap-4 text-xs text-neutral-400 mb-3">
                                                        <span>Created: {formatDate(alert.created_at)}</span>
                                                        {alert.company_name && (
                                                            <>
                                                                <span>•</span>
                                                                <span>Company: {alert.company_name}</span>
                                                            </>
                                                        )}
                                                        {alert.acknowledged_by && (
                                                            <>
                                                                <span>•</span>
                                                                <span>Acknowledged by: {alert.acknowledged_by}</span>
                                                            </>
                                                        )}
                                                        {alert.resolution_notes && (
                                                            <div className="w-full p-2 bg-emerald-500/10 border border-emerald-500/20 rounded text-emerald-300 text-xs mt-2">
                                                                <strong>Resolution:</strong> {alert.resolution_notes}
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Actions */}
                                                    {isOpen && (
                                                        <div className="flex items-center gap-2">
                                                            <button
                                                                onClick={() => handleAcknowledge(alert.id)}
                                                                className="text-xs px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 rounded transition-colors"
                                                            >
                                                                Acknowledge
                                                            </button>
                                                            <button
                                                                onClick={() => handleResolve(alert.id)}
                                                                className="text-xs px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded transition-colors"
                                                            >
                                                                Mark Resolved
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>

                                                <div className="text-xs text-neutral-500">
                                                    {formatDate(alert.created_at)}
                                                </div>
                                            </div>
                                        </AgencyCard>
                                    </motion.div>
                                )
                            })}
                        </div>
                    ))}
                </div>
            )}

            {/* Info Banner */}
            <AgencyCard variant="glass" className="p-4">
                <div className="flex items-start gap-3">
                    <Bell className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
                    <div className="text-sm text-neutral-300">
                        <p className="font-medium text-white mb-1">Webhook Notifications</p>
                        <p className="text-neutral-400">
                            Get real-time alerts via webhook. Configure webhook endpoints in Settings to receive
                            JSON payloads for critical events like low credits, health score drops, and new company onboarding.
                        </p>
                    </div>
                </div>
            </AgencyCard>
        </div>
    )
}
