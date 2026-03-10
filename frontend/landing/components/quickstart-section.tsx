'use client'

import { useState } from 'react'

const TERMINAL_LINES = [
  { text: '$ pip install mekong-cli', color: 'text-cyan-300' },
  { text: '$ mekong start', color: 'text-cyan-300' },
  { text: '', color: '' },
  { text: '🏯 Chào mừng! Bạn là ai?', color: 'text-white' },
  { text: '  1. 👑 Founder / CEO', color: 'text-yellow-400' },
  { text: '  2. 🏢 Business Manager', color: 'text-blue-400' },
  { text: '  3. 📦 Product Manager', color: 'text-purple-400' },
  { text: '  4. ⚙️  Developer', color: 'text-cyan-400' },
  { text: '  5. 🔧 Operations', color: 'text-green-400' },
  { text: '> 1', color: 'text-slate-300' },
  { text: '', color: '' },
  { text: '👑 Founder commands:', color: 'text-yellow-400' },
  { text: '  /annual    — Kế hoạch kinh doanh năm', color: 'text-slate-300' },
  { text: '  /okr       — Đặt mục tiêu OKR', color: 'text-slate-300' },
  { text: '  /fundraise — Chuẩn bị gọi vốn', color: 'text-slate-300' },
]

const INSTALL_CMD = 'pip install mekong-cli'

export default function QuickstartSection() {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(INSTALL_CMD).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <section id="quickstart" className="px-6 py-20">
      <div className="mx-auto max-w-2xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Bắt đầu trong{' '}
            <span className="gradient-text">30 giây</span>
          </h2>
          <p className="text-slate-400">
            Cài đặt, chọn vai trò, bắt đầu. Không cần config phức tạp.
          </p>
        </div>

        <div className="glass glow-blue overflow-hidden rounded-2xl">
          {/* Terminal title bar */}
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-red-500/80" />
              <span className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <span className="h-3 w-3 rounded-full bg-green-500/80" />
              <span className="ml-2 text-xs text-slate-500">mekong-cli — zsh</span>
            </div>
            <button
              onClick={handleCopy}
              className="rounded-md border border-slate-700 px-3 py-1 text-xs text-slate-400 transition-colors hover:border-slate-500 hover:text-white"
            >
              {copied ? '✓ Copied' : 'Copy install'}
            </button>
          </div>

          {/* Terminal body */}
          <div className="p-5 font-mono text-sm">
            {TERMINAL_LINES.map((line, i) => (
              <div key={i} className={`leading-6 ${line.color}`}>
                {line.text || '\u00A0'}
              </div>
            ))}
            <span className="terminal-cursor text-cyan-400" />
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-slate-600">
          Python 3.11+ required. Works on macOS, Linux, Windows (WSL).
        </p>
      </div>
    </section>
  )
}
