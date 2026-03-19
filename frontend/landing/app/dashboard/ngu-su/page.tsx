'use client'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

const FACTORS = [
  { key: 'dao_score', label: 'Dao', desc: 'Mission alignment' },
  { key: 'thien_score', label: 'Thien', desc: 'Market timing' },
  { key: 'dia_score', label: 'Dia', desc: 'Competitive landscape' },
  { key: 'tuong_score', label: 'Tuong', desc: 'Leadership quality' },
  { key: 'phap_score', label: 'Phap', desc: 'Process & operations' },
]

const TERRAIN_LABELS: Record<string, string> = {
  tu_dia: 'Tu Dia (Critical)', vi_dia: 'Vi Dia (Hemmed)',
  tranh_dia: 'Tranh Dia (Contested)', giao_dia: 'Giao Dia (Stable)',
  unknown: 'Chua phan loai',
}

export default function NguSuPage() {
  const [scores, setScores] = useState<any[]>([])

  useEffect(() => {
    api.getNguSu().then(r => setScores(r.scores || [])).catch(console.error)
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Ngu Su — Portfolio Health</h1>
      {scores.map((s: any) => (
        <div key={s.id} className="rounded-xl border border-[var(--md-outline-variant)] bg-[var(--md-surface-container-low)] p-5">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">{s.entity_name}</h2>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded-full bg-violet-500/10 text-violet-400">
                {TERRAIN_LABELS[s.terrain] || s.terrain}
              </span>
              <span className={`text-lg font-bold ${
                s.overall_score >= 3.5 ? 'text-emerald-400' : s.overall_score >= 2.5 ? 'text-amber-400' : 'text-red-400'
              }`}>{Number(s.overall_score).toFixed(1)}/5.0</span>
            </div>
          </div>
          {FACTORS.map(f => {
            const val = s[f.key] || 0
            return (
              <div key={f.key} className="flex items-center gap-2 mb-1.5">
                <span className="w-20 text-xs text-right">{f.label}</span>
                <div className="flex-1 h-4 bg-[var(--md-surface-container)] rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${
                    val >= 3.5 ? 'bg-emerald-500/40' : val >= 2.5 ? 'bg-amber-500/40' : 'bg-red-500/40'
                  }`} style={{ width: `${(val / 5) * 100}%` }}>
                    <span className="text-[10px] px-1">{val.toFixed(1)}</span>
                  </div>
                </div>
                <span className="w-32 text-[10px] text-[var(--md-on-surface-variant)]">{f.desc}</span>
              </div>
            )
          })}
        </div>
      ))}
      {scores.length === 0 && <p className="text-sm text-[var(--md-on-surface-variant)]">Chua co portfolio nao duoc danh gia Ngu Su.</p>}
    </div>
  )
}
