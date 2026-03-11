'use client'

import { useState } from 'react'

const TERMINAL_LINES = [
  { text: '$ mekong cook "Create a landing page for a café"', color: 'text-cyan-300' },
  { text: '', color: '' },
  { text: '  💡 Using: LLM_BASE_URL=openrouter.ai', color: 'text-slate-500' },
  { text: '  🎯 Goal: Landing page for a café', color: 'text-white' },
  { text: '  🤖 Agent: cto via claude-sonnet-4-6', color: 'text-slate-300' },
  { text: '  📋 Steps:', color: 'text-slate-300' },
  { text: '    1. Research café landing best practices', color: 'text-slate-400' },
  { text: '    2. Generate responsive HTML/CSS', color: 'text-slate-400' },
  { text: '    3. Deploy to Cloudflare Pages', color: 'text-slate-400' },
  { text: '  ⚡ Executing...', color: 'text-yellow-400' },
  { text: '', color: '' },
  { text: '  ✅ Done: https://cafe-landing.pages.dev', color: 'text-green-400' },
  { text: '  💳 MCU: -3 (balance: 197)', color: 'text-purple-400' },
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
            Get started in{' '}
            <span className="gradient-text">30 seconds</span>
          </h2>
          <p className="text-slate-400">
            Install, pick a role, start. No complex configuration.
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
          Python 3.9+ required. Works on macOS, Linux, Windows (WSL).
        </p>
      </div>
    </section>
  )
}
