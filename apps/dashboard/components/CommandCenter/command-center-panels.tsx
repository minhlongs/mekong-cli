'use client'

import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Terminal, CheckCircle2, AlertCircle, Clock, Activity } from 'lucide-react'

export interface AgentStatus {
  name: string
  status: 'ready' | 'running' | 'error' | 'idle'
  lastRun?: string
  icon: React.ReactNode
  color: string
}

export interface CommandAction {
  id: string
  label: string
  command: string
  icon: React.ReactNode
  color: string
  description: string
}

export interface CommandButtonProps {
  command: CommandAction
  isActive: boolean
  onClick: () => void
}

export function CommandButton({ command, isActive, onClick }: CommandButtonProps) {
  const colorClasses: Record<string, string> = {
    purple: 'from-purple-500/20 to-pink-500/20 border-purple-500/30 hover:border-purple-500/50',
    green: 'from-green-500/20 to-emerald-500/20 border-green-500/30 hover:border-green-500/50',
    orange: 'from-orange-500/20 to-red-500/20 border-orange-500/30 hover:border-orange-500/50',
  }

  const iconColors: Record<string, string> = {
    purple: 'text-purple-400',
    green: 'text-green-400',
    orange: 'text-orange-400',
  }

  return (
    <motion.button
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={isActive}
      className={`relative p-6 rounded-2xl bg-gradient-to-br ${colorClasses[command.color]} border backdrop-blur-sm transition-all overflow-hidden group`}
    >
      {isActive && (
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: '100%' }}
          transition={{ duration: 1.5 }}
          className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-white/50 to-white/20"
        />
      )}

      <div className="flex flex-col items-center gap-3">
        <div
          className={`p-3 rounded-xl bg-black/20 ${iconColors[command.color]} group-hover:scale-110 transition-transform`}
        >
          {command.icon}
        </div>
        <span className="text-lg font-bold text-white">{command.label}</span>
        <span className="text-xs text-neutral-400">{command.description}</span>
      </div>
    </motion.button>
  )
}

function getStatusColor(status: AgentStatus['status']) {
  switch (status) {
    case 'ready':
      return 'text-green-400'
    case 'running':
      return 'text-blue-400 animate-pulse'
    case 'error':
      return 'text-red-400'
    case 'idle':
      return 'text-neutral-500'
  }
}

function getStatusIcon(status: AgentStatus['status']) {
  switch (status) {
    case 'ready':
      return <CheckCircle2 className="w-3 h-3 text-green-400" />
    case 'running':
      return <Activity className="w-3 h-3 text-blue-400 animate-pulse" />
    case 'error':
      return <AlertCircle className="w-3 h-3 text-red-400" />
    case 'idle':
      return <Clock className="w-3 h-3 text-neutral-500" />
  }
}

export function AgentStatusGrid({ agents }: { agents: AgentStatus[] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 rounded-2xl bg-gradient-to-br from-neutral-800/80 to-neutral-900/80 border border-white/10 backdrop-blur-xl"
    >
      <h3 className="text-sm font-medium text-neutral-400 mb-4 flex items-center gap-2">
        <Activity className="w-4 h-4" />
        Agent Status
      </h3>

      <div className="grid grid-cols-2 gap-3">
        {agents.map((agent, index) => (
          <motion.div
            key={agent.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-4 rounded-xl bg-neutral-900/50 border border-white/5 hover:border-white/10 transition-all"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className={`text-${agent.color}-400`}>{agent.icon}</span>
                <span className="text-sm font-medium text-white">{agent.name}</span>
              </div>
              {getStatusIcon(agent.status)}
            </div>
            <span className={`text-xs capitalize ${getStatusColor(agent.status)}`}>
              {agent.status}
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

export function LiveLogsPanel({ logs }: { logs: string[] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="p-6 rounded-2xl bg-neutral-900/80 border border-white/10"
    >
      <h3 className="text-sm font-medium text-neutral-400 mb-4 flex items-center gap-2">
        <Terminal className="w-4 h-4" />
        Live Logs
      </h3>

      <div className="bg-black/50 rounded-xl p-4 font-mono text-xs h-32 overflow-y-auto">
        <AnimatePresence>
          {logs.map((log, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-neutral-300 py-0.5"
            >
              {log}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
