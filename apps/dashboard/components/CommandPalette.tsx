'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Command, Zap, Play } from 'lucide-react'
import { logger } from '@/lib/utils/logger'
import { resolveEngineApiUrl } from '@/lib/demo-guard'
import {
  type CommandItem,
  type CommandSuite,
  type FlattenedCommand,
  type CommandResult,
  type CommandPaletteProps,
  COMMAND_SUITES,
  ALL_COMMANDS,
} from './command-palette-items'

export type { CommandItem, CommandSuite, FlattenedCommand, CommandResult, CommandPaletteProps }
export { COMMAND_SUITES, ALL_COMMANDS }

const API_BASE = resolveEngineApiUrl()

export default function CommandPalette({ isOpen, onClose, onExecute }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [executing, setExecuting] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<CommandResult | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const q = query.toLowerCase()
  const filteredCommands = ALL_COMMANDS.filter(
    cmd => cmd.cmd.toLowerCase().includes(q) || cmd.desc.toLowerCase().includes(q) || cmd.suite.toLowerCase().includes(q)
  )

  const executeCommand = useCallback(
    async (command: string) => {
      setExecuting(command)
      try {
        const response = await fetch(`${API_BASE}/command/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: command.replace('/', ''), params: {} }),
        })
        const result = await response.json()
        setLastResult(result)
        onExecute?.(command, result)
      } catch (error) {
        logger.error('Command execution failed', error)
        setLastResult({ success: false, error: 'Connection failed' })
      } finally {
        setExecuting(null)
      }
    },
    [onExecute]
  )

  useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(i => Math.min(i + 1, filteredCommands.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(i => Math.max(i - 1, 0))
      } else if (e.key === 'Enter') {
        e.preventDefault()
        if (filteredCommands[selectedIndex]) executeCommand(filteredCommands[selectedIndex].cmd)
      } else if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filteredCommands, selectedIndex, executeCommand, onClose])

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus()
      setQuery('')
      setSelectedIndex(0)
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-2xl bg-gray-900/95 border border-gray-700/50 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in slide-in-from-top-4 duration-200">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-800">
          <Command className="w-5 h-5 text-emerald-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => {
              setQuery(e.target.value)
              setSelectedIndex(0)
            }}
            placeholder="Type a command... (135 available)"
            className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-lg"
          />
          <span className="text-xs text-gray-500 px-2 py-1 bg-gray-800 rounded">ESC</span>
        </div>

        {lastResult && (
          <div
            className={`px-4 py-2 text-sm ${lastResult.success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}
          >
            {lastResult.success ? '✅ ' : '❌ '}
            {lastResult.binh_phap && <span className="mr-2">🏯 {lastResult.binh_phap}</span>}
            {lastResult.command || lastResult.error}
          </div>
        )}

        <div className="max-h-[400px] overflow-y-auto">
          {filteredCommands.slice(0, 20).map((cmd, index) => (
            <div
              key={cmd.cmd}
              className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-all ${
                index === selectedIndex
                  ? 'bg-emerald-500/20 border-l-2 border-emerald-400'
                  : 'hover:bg-gray-800/50'
              }`}
              onClick={() => executeCommand(cmd.cmd)}
            >
              <span className="text-2xl">{cmd.icon}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <code className="text-emerald-400 font-mono">{cmd.cmd}</code>
                  {executing === cmd.cmd && <span className="animate-spin text-amber-400">⚡</span>}
                </div>
                <p className="text-sm text-gray-400">{cmd.desc}</p>
              </div>
              <div className="text-right">
                <span className="text-xs text-gray-500">{cmd.suite}</span>
                <div className="text-xs text-gray-600">{cmd.binh_phap}</div>
              </div>
              <Play className="w-4 h-4 text-gray-600 group-hover:text-emerald-400" />
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between px-4 py-2 border-t border-gray-800 text-xs text-gray-500">
          <div className="flex items-center gap-4">
            <span>↑↓ Navigate</span>
            <span>↵ Execute</span>
            <span>ESC Close</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="w-3 h-3 text-emerald-400" />
            <span>{filteredCommands.length} / 143 commands</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(prev => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])
  return { isOpen, setIsOpen }
}
