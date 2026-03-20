'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Plus, FileText, Clock, TrendingUp, Zap, MoreVertical } from 'lucide-react'
import { supabase, type Proposal } from '@/lib/supabase'

export const dynamic = 'force-dynamic'

export default function DashboardPage() {
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProposals()
  }, [])

  async function loadProposals() {
    try {
      const { data, error } = await supabase
        .from('proposals')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10)

      if (error) throw error
      setProposals(data || [])
    } catch (error) {
      console.error('Error loading proposals:', error)
    } finally {
      setLoading(false)
    }
  }

  const stats = {
    total: proposals.length,
    thisWeek: proposals.filter(p => {
      const weekAgo = new Date()
      weekAgo.setDate(weekAgo.getDate() - 7)
      return new Date(p.created_at) > weekAgo
    }).length,
    winRate: '42%'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Zap className="h-6 w-6 text-purple-600" />
              <span className="font-bold text-xl">Sophia AI Factory</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/brand-voice" className="text-sm text-gray-600 hover:text-gray-900">
                Brand Voice
              </Link>
              <Link href="/auth/login" className="text-sm text-gray-600 hover:text-gray-900">
                Sign Out
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            icon={<FileText className="h-5 w-5 text-purple-600" />}
            label="Total Proposals"
            value={stats.total.toString()}
          />
          <StatCard
            icon={<Clock className="h-5 w-5 text-green-600" />}
            label="This Week"
            value={stats.thisWeek.toString()}
          />
          <StatCard
            icon={<TrendingUp className="h-5 w-5 text-blue-600" />}
            label="Win Rate"
            value={stats.winRate}
          />
        </div>

        {/* Proposals List */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b flex justify-between items-center">
            <h2 className="text-lg font-semibold">Recent Proposals</h2>
            <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition text-sm">
              <Plus className="h-4 w-4" />
              New Proposal
            </button>
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : proposals.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-500 mb-4">No proposals yet</p>
              <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition text-sm">
                Create Your First Proposal
              </button>
            </div>
          ) : (
            <div className="divide-y">
              {proposals.map((proposal) => (
                <div
                  key={proposal.id}
                  className="p-4 flex items-center justify-between hover:bg-gray-50 transition"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                      <FileText className="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-medium">{proposal.title}</h3>
                      <p className="text-sm text-gray-500">
                        {proposal.client_name || 'No client name'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <StatusBadge status={proposal.status} />
                    <button className="p-2 hover:bg-gray-200 rounded-full">
                      <MoreVertical className="h-4 w-4 text-gray-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <span className="text-sm text-gray-600">{label}</span>
      </div>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700',
    pending: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
    sent: 'bg-blue-100 text-blue-700'
  }

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${styles[status] || styles.draft}`}>
      {status}
    </span>
  )
}
