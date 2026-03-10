'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { COMMANDS } from '@/data/commands'
import { LAYERS } from '@/data/layers'

const CREDIT_DOTS: Record<number, string> = {
  0: 'Miễn phí',
  1: '●',
  2: '●●',
  3: '●●●',
  4: '●●●●',
  5: '●●●●●',
}

const COMPLEXITY_COLOR: Record<string, string> = {
  trivial: 'text-slate-400 bg-slate-800',
  simple: 'text-green-400 bg-green-900/30',
  standard: 'text-blue-400 bg-blue-900/30',
  complex: 'text-purple-400 bg-purple-900/30',
}

const LAYER_COLOR: Record<string, string> = {
  founder: 'text-cyan-400',
  business: 'text-blue-400',
  product: 'text-purple-400',
  engineering: 'text-green-400',
  ops: 'text-orange-400',
}

const ALL_TAB = { id: 'all', icon: '⊞', role: 'All' }

export default function CommandsPage() {
  const [search, setSearch] = useState('')
  const [activeLayer, setActiveLayer] = useState('all')

  const tabs = [ALL_TAB, ...LAYERS.map((l) => ({ id: l.id, icon: l.icon, role: l.role }))]

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    return COMMANDS.filter((cmd) => {
      const matchLayer = activeLayer === 'all' || cmd.layer === activeLayer
      const matchSearch =
        !q ||
        cmd.id.toLowerCase().includes(q) ||
        cmd.displayName.toLowerCase().includes(q) ||
        cmd.description.toLowerCase().includes(q)
      return matchLayer && matchSearch
    })
  }, [search, activeLayer])

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-16 sm:px-6">
      <div className="mx-auto max-w-6xl">
        {/* Back nav */}
        <Link
          href="/"
          className="mb-8 inline-flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors"
        >
          ← Trang chủ
        </Link>

        {/* Hero */}
        <div className="mb-10 text-center">
          <h1 className="mb-3 text-3xl font-bold sm:text-4xl">
            <span className="gradient-text">Command Explorer</span>
          </h1>
          <p className="text-slate-400">
            {COMMANDS.length} lệnh — tìm kiếm theo tên, mô tả hoặc layer
          </p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Tìm lệnh... (cook, deploy, fundraise...)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full glass rounded-xl px-5 py-3 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-cyan-400/40 border border-transparent transition-colors"
          />
        </div>

        {/* Layer tabs */}
        <div className="mb-8 flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveLayer(tab.id)}
              className={`flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm transition-all ${
                activeLayer === tab.id
                  ? 'glass-highlight text-cyan-400 font-semibold'
                  : 'glass-card text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>{tab.icon}</span>
              <span className="hidden sm:inline">{tab.role.split(' ')[0]}</span>
            </button>
          ))}
        </div>

        {/* Count */}
        <p className="mb-4 text-xs text-slate-500">
          Hiển thị {filtered.length} / {COMMANDS.length} lệnh
        </p>

        {/* Grid */}
        {filtered.length === 0 ? (
          <div className="glass-card rounded-xl p-10 text-center text-slate-500">
            Không tìm thấy lệnh phù hợp — thử từ khóa khác
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((cmd) => (
              <div key={cmd.id} className="glass-card rounded-xl p-4">
                {/* Name + layer */}
                <div className="mb-2 flex items-start justify-between gap-2">
                  <span className="font-mono text-sm font-bold text-slate-100">
                    {cmd.id}
                  </span>
                  <span
                    className={`shrink-0 text-xs font-medium ${LAYER_COLOR[cmd.layer] ?? 'text-slate-400'}`}
                  >
                    {LAYERS.find((l) => l.id === cmd.layer)?.icon ?? ''}{' '}
                    {cmd.layer}
                  </span>
                </div>

                {/* Description */}
                <p className="mb-3 text-xs text-slate-400 leading-relaxed">
                  {cmd.description}
                </p>

                {/* Badges */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${COMPLEXITY_COLOR[cmd.complexity] ?? 'text-slate-400 bg-slate-800'}`}
                  >
                    {cmd.complexity}
                  </span>
                  <span className="text-xs text-slate-500">
                    {cmd.creditCost === 0 ? (
                      <span className="text-green-400">Free</span>
                    ) : (
                      <span className="text-yellow-500 tracking-widest">
                        {CREDIT_DOTS[cmd.creditCost] ?? cmd.creditCost}
                      </span>
                    )}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer nav */}
        <div className="mt-12 flex flex-wrap gap-4 justify-center">
          <Link
            href="/dev/quickstart"
            className="glass-card rounded-lg px-5 py-2.5 text-sm text-slate-300 hover:text-cyan-400 transition-colors"
          >
            ← Quickstart
          </Link>
          <Link
            href="/dev/architecture"
            className="glass-card rounded-lg px-5 py-2.5 text-sm text-slate-300 hover:text-cyan-400 transition-colors"
          >
            Architecture →
          </Link>
        </div>
      </div>
    </main>
  )
}
