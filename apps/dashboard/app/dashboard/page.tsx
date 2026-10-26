'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { ShieldCheck, PackageCheck, ArrowUpRight, DollarSign, Activity, Lock } from 'lucide-react'
import Link from 'next/link'
import { CommandCenter, StatusLine } from '@/components/CommandCenter'
import { UnifiedBridgeWidget } from '@/components/antigravity'
import { AgencyCard } from '@/components/ui/agency-card'

const METRICS = [
    {
        label: 'Dual-Rail Revenue (ARR)',
        value: '$124,500',
        change: 'VietQR + USDT',
        trend: 'up',
        icon: DollarSign,
        color: 'from-emerald-500 to-teal-500',
    },
    {
        label: 'Verified Business Packs',
        value: 'opc-pack/v1',
        change: '4 Active',
        trend: 'up',
        icon: PackageCheck,
        color: 'from-blue-500 to-indigo-500',
    },
    {
        label: 'SHA-256 Approval Gate',
        value: '100% Bound',
        change: 'Zero Replay',
        trend: 'up',
        icon: ShieldCheck,
        color: 'from-purple-500 to-pink-500',
    },
    {
        label: 'Open-Core Blueprint',
        value: '25/25 READY',
        change: 'SQLite WAL',
        trend: 'neutral',
        icon: Activity,
        color: 'from-emerald-500 to-cyan-500',
    },
]

export default function DashboardPage() {
    return (
        <div className="space-y-6">
            {/* Status Line */}
            <StatusLine />

            {/* Sovereign OPC 2027 Hero Banner */}
            <AgencyCard variant="glass-pro" className="p-6 border border-emerald-500/30 bg-gradient-to-r from-emerald-500/10 via-[#0b0f17] to-[#0b0f17]">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-0.5 text-[10px] font-mono text-emerald-400 uppercase mb-2">
                            <Lock className="w-3 h-3" />
                            OPC 2027 Sovereign Operating System
                        </div>
                        <h2 className="text-xl font-bold text-white">
                            Agentic Cockpit &amp; Cryptographic Approval Gate
                        </h2>
                        <p className="text-xs text-neutral-400 mt-1 max-w-2xl">
                            Execute declarative business packs (<code className="text-emerald-300">opc-pack/v1</code>) with payload-bound SHA-256 human approvals, honest usage economics, and Dual-Rail RaaS settlement.
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-3 shrink-0">
                        <Link
                            href="/dashboard/opc"
                            className="rounded-xl bg-emerald-500 px-4 py-2.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 flex items-center gap-1.5 transition-colors"
                        >
                            <span>Launch OPC Cockpit</span>
                            <ArrowUpRight className="w-4 h-4" />
                        </Link>
                        <Link
                            href="/dashboard/packs"
                            className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs font-semibold text-white hover:bg-white/10 transition-colors"
                        >
                            Packs Registry
                        </Link>
                    </div>
                </div>
            </AgencyCard>

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {METRICS.map((metric, idx) => (
                    <motion.div
                        key={metric.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                    >
                        <AgencyCard variant="glass-pro" className="relative overflow-hidden group hover-lift">
                            <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                                <metric.icon className="w-12 h-12 text-white" />
                            </div>
                            <div className="relative z-10">
                                <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${metric.color} flex items-center justify-center mb-3 shadow-lg`}>
                                    <metric.icon className="w-4 h-4 text-white" />
                                </div>
                                <p className="text-neutral-400 text-xs font-medium">{metric.label}</p>
                                <div className="flex items-end gap-2 mt-1">
                                    <h3 className="text-xl font-bold text-white">{metric.value}</h3>
                                    <span className="text-xs font-mono font-medium mb-0.5 text-emerald-400 flex items-center">
                                        {metric.change}
                                        {metric.trend === 'up' && <ArrowUpRight className="w-3 h-3 ml-0.5" />}
                                    </span>
                                </div>
                            </div>
                        </AgencyCard>
                    </motion.div>
                ))}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Command Center - Takes 2 columns */}
                <div className="lg:col-span-2">
                    <CommandCenter />
                </div>

                {/* Right Sidebar */}
                <div className="space-y-6">
                    {/* Unified Bridge Widget */}
                    <UnifiedBridgeWidget />

                    {/* Strategic Alerts */}
                    <AgencyCard variant="glass" className="p-5">
                        <h3 className="text-sm font-bold text-white mb-4">OPC Governance Ledger</h3>
                        <div className="space-y-3">
                            {[
                                { title: 'SHA-256 Digest Verified', desc: 'client-proposal-followup bound', time: 'Live' },
                                { title: 'Honest Usage Ledger', desc: 'has_unknown_costs=False', time: 'Synced' },
                                { title: 'Dual-Rail Gateway', desc: 'VietQR Napas 247 + NOWPayments', time: 'Active' },
                            ].map((item, i) => (
                                <div key={i} className="flex gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer group">
                                    <div className="w-1.5 h-1.5 mt-1.5 rounded-full bg-emerald-500 shrink-0 group-hover:scale-125 transition-transform" />
                                    <div>
                                        <h4 className="text-xs font-medium text-white group-hover:text-emerald-400 transition-colors">{item.title}</h4>
                                        <p className="text-[10px] font-mono text-neutral-400">{item.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </AgencyCard>
                </div>
            </div>
        </div>
    )
}
