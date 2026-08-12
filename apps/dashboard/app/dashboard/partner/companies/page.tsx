'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Plus, ExternalLink, Building2, Trash2, Edit2 } from 'lucide-react'
import { AgencyCard } from '@/components/ui/agency-card'

interface PartnerCompany {
    id: string
    name: string
    email_domain?: string
    health_score: number
    credit_allocated: number
    credit_consumed: number
    days_since_active: number
    onboarded: boolean
    industry?: string
    company_size?: string
}

export default function PartnerCompaniesPage() {
    const [companies, setCompanies] = useState<PartnerCompany[]>([])
    const [loading, setLoading] = useState(true)
    const [showAddModal, setShowAddModal] = useState(false)
    const [newCompany, setNewCompany] = useState({
        name: '',
        email_domain: '',
        industry: '',
        company_size: 'startup'
    })
    const [submitting, setSubmitting] = useState(false)

    const fetchCompanies = async () => {
        try {
            const response = await fetch('/api/v1/partner/portfolio')
            if (response.ok) {
                setCompanies(await response.json())
            }
        } catch (error) {
            console.error('Error fetching companies:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchCompanies()
    }, [])

    const handleAddCompany = async (e: React.FormEvent) => {
        e.preventDefault()
        setSubmitting(true)

        try {
            const response = await fetch('/api/v1/partner/companies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newCompany)
            })

            if (!response.ok) {
                throw new Error('Failed to add company')
            }

            setShowAddModal(false)
            setNewCompany({ name: '', email_domain: '', industry: '', company_size: 'startup' })
            fetchCompanies()
        } catch (error) {
            console.error('Error adding company:', error)
            alert('Failed to add company')
        } finally {
            setSubmitting(false)
        }
    }

    const handleRemoveCompany = async (companyId: string, companyName: string) => {
        if (!confirm(`Are you sure you want to remove "${companyName}" from your portfolio?`)) {
            return
        }

        try {
            const response = await fetch(`/api/v1/partner/companies/${companyId}`, {
                method: 'DELETE'
            })

            if (!response.ok) {
                throw new Error('Failed to remove company')
            }

            setCompanies(companies.filter(c => c.id !== companyId))
        } catch (error) {
            console.error('Error removing company:', error)
            alert('Failed to remove company')
        }
    }

    const handleAllocateCredits = async (companyId: string, additionalCredits: number) => {
        try {
            const response = await fetch(`/api/v1/partner/companies/${companyId}/credits`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ additional_credits: additionalCredits })
            })

            if (!response.ok) {
                throw new Error('Failed to allocate credits')
            }

            fetchCompanies()
        } catch (error) {
            console.error('Error allocating credits:', error)
            alert('Failed to allocate credits')
        }
    }

    const getHealthColor = (score: number) => {
        if (score >= 0.7) return 'text-emerald-400'
        if (score >= 0.4) return 'text-amber-400'
        return 'text-red-400'
    }

    const getHealthLabel = (score: number) => {
        if (score >= 0.7) return 'Healthy'
        if (score >= 0.5) return 'At Risk'
        if (score > 0) return 'Critical'
        return 'Inactive'
    }

    const calculateUtilization = (consumed: number, allocated: number) => {
        if (allocated === 0) return 0
        return Math.round((consumed / allocated) * 100)
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-neutral-400">Loading companies...</div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Portfolio Companies</h1>
                    <p className="text-neutral-400 text-sm mt-1">
                        Manage companies under your partner program
                    </p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors"
                >
                    <Plus className="w-4 h-4" />
                    Add Company
                </button>
            </div}

            {/* Stats Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <AgencyCard variant="glass" className="p-4 text-center">
                    <p className="text-2xl font-bold text-white">{companies.length}</p>
                    <p className="text-sm text-neutral-400">Total Companies</p>
                </AgencyCard>
                <AgencyCard variant="glass" className="p-4 text-center">
                    <p className="text-2xl font-bold text-emerald-400">
                        {companies.filter(c => c.onboarded).length}
                    </p>
                    <p className="text-sm text-neutral-400">Onboarded</p>
                </AgencyCard>
                <AgencyCard variant="glass" className="p-4 text-center">
                    <p className="text-2xl font-bold text-amber-400">
                        {companies.filter(c => !c.onboarded).length}
                    </p>
                    <p className="text-sm text-neutral-400">Pending Onboarding</p>
                </AgencyCard>
                <AgencyCard variant="glass" className="p-4 text-center">
                    <p className="text-2xl font-bold text-blue-400">
                        {companies.reduce((sum, c) => sum + c.credit_consumed, 0).toLocaleString()}
                    </p>
                    <p className="text-sm text-neutral-400">Total Credits Used</p>
                </AgencyCard>
            </div>

            {/* Companies Table */}
            {companies.length === 0 ? (
                <AgencyCard variant="glass" className="p-8 text-center">
                    <Building2 className="w-12 h-12 text-neutral-600 mx-auto mb-3" />
                    <p className="text-neutral-300 font-medium">No companies added</p>
                    <p className="text-neutral-400 text-sm mb-4">
                        Add companies to start monitoring their usage and health
                    </p>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm transition-colors"
                    >
                        Add Your First Company
                    </button>
                </AgencyCard>
            ) : (
                <div className="space-y-3">
                    {companies.map((company, idx) => (
                        <motion.div
                            key={company.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.05 }}
                        >
                            <AgencyCard variant="glass" className="p-4">
                                <div className="flex flex-col lg:flex-row gap-4 lg:items-center justify-between">
                                    {/* Company Info */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Building2 className="w-4 h-4 text-neutral-500" />
                                            <h3 className="font-semibold text-white truncate">{company.name}</h3>
                                            {!company.onboarded && (
                                                <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded-full">
                                                    Pending
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-400">
                                            {company.email_domain && (
                                                <span>{company.email_domain}</span>
                                            )}
                                            {company.industry && (
                                                <>
                                                    <span>•</span>
                                                    <span>{company.industry}</span>
                                                </>
                                            )}
                                            <span>•</span>
                                            <span className={getHealthColor(company.health_score)}>
                                                {getHealthLabel(company.health_score)}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Health & Usage */}
                                    <div className="flex items-center gap-6">
                                        <div className="text-center">
                                            <div className={`text-lg font-bold ${getHealthColor(company.health_score)}`}>
                                                {(company.health_score * 100).toFixed(0)}%
                                            </div>
                                            <div className="text-xs text-neutral-400">Health Score</div>
                                        </div>
                                        <div className="text-center">
                                            <div className="text-lg font-bold text-white">
                                                {calculateUtilization(company.credit_consumed, company.credit_allocated)}%
                                            </div>
                                            <div className="text-xs text-neutral-400">Credit Usage</div>
                                            <div className="w-16 h-1.5 bg-neutral-700 rounded-full mt-1 overflow-hidden">
                                                <div
                                                    className="h-full bg-emerald-500 rounded-full transition-all"
                                                    style={{ width: `${calculateUtilization(company.credit_consumed, company.credit_allocated)}%` }}
                                                />
                                            </div>
                                        </div>
                                        <div className="text-center">
                                            <div className="text-lg font-bold text-white">
                                                {company.credit_consumed} / {company.credit_allocated}
                                            </div>
                                            <div className="text-xs text-neutral-400">Credits</div>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center gap-2">
                                        <a
                                            href={`/dashboard/partner/companies/${company.id}`}
                                            className="flex items-center gap-1 px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-sm rounded-lg transition-colors"
                                        >
                                            <ExternalLink className="w-3 h-3" />
                                            Details
                                        </a>
                                        <button
                                            onClick={() => handleAllocateCredits(company.id, 100)}
                                            className="flex items-center gap-1 px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-sm rounded-lg transition-colors"
                                            title="Add 100 credits"
                                        >
                                            <Plus className="w-3 h-3" />
                                            +100
                                        </button>
                                        <button
                                            onClick={() => handleRemoveCompany(company.id, company.name)}
                                            className="p-1.5 text-neutral-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                                            title="Remove company"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>

                                {/* Inactivity Warning */}
                                {company.days_since_active >= 14 && (
                                    <div className="mt-3 p-2 bg-amber-500/10 border border-amber-500/20 rounded text-xs text-amber-400">
                                        <AlertCircle className="w-3 h-3 inline mr-1" />
                                        Inactive for {company.days_since_active} days
                                    </div>
                                )}
                            </AgencyCard>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Add Company Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="w-full max-w-md"
                    >
                        <AgencyCard variant="glass" className="p-6">
                            <h2 className="text-xl font-bold text-white mb-4">Add Company</h2>
                            <form onSubmit={handleAddCompany} className="space-y-4">
                                <div>
                                    <label className="block text-sm text-neutral-400 mb-1">Company Name *</label>
                                    <input
                                        type="text"
                                        required
                                        value={newCompany.name}
                                        onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500"
                                        placeholder="Acme Corp"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-neutral-400 mb-1">Email Domain</label>
                                    <input
                                        type="text"
                                        value={newCompany.email_domain}
                                        onChange={(e) => setNewCompany({ ...newCompany, email_domain: e.target.value })}
                                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500"
                                        placeholder="acme.com"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-neutral-400 mb-1">Industry</label>
                                    <select
                                        value={newCompany.industry}
                                        onChange={(e) => setNewCompany({ ...newCompany, industry: e.target.value })}
                                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                                    >
                                        <option value="">Select industry...</option>
                                        <option value="technology">Technology</option>
                                        <option value="finance">Finance</option>
                                        <option value="healthcare">Healthcare</option>
                                        <option value="retail">Retail</option>
                                        <option value="education">Education</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm text-neutral-400 mb-1">Company Size</label>
                                    <select
                                        value={newCompany.company_size}
                                        onChange={(e) => setNewCompany({ ...newCompany, company_size: e.target.value })}
                                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                                    >
                                        <option value="startup">Startup</option>
                                        <option value="smb">SMB</option>
                                        <option value="enterprise">Enterprise</option>
                                    </select>
                                </div>
                                <div className="flex gap-3 pt-4">
                                    <button
                                        type="button"
                                        onClick={() => setShowAddModal(false)}
                                        className="flex-1 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={submitting}
                                        className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors disabled:opacity-50"
                                    >
                                        {submitting ? 'Adding...' : 'Add Company'}
                                    </button>
                                </div>
                            </form>
                        </AgencyCard>
                    </motion.div>
                </div>
            )}
        </div>
    )
}
