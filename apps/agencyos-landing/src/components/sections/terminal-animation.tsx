"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";

const codeLines = [
  '$ npm install @agencyos/raas',
  '✓ Installing dependencies...',
  '✓ Setting up AI agents...',
  '✓ Connecting to knowledge base...',
  '> Ready! Your RaaS is live 🚀',
];

export function TerminalAnimation() {
  const [lines, setLines] = useState<string[]>([]);

  useEffect(() => {
    let lineIndex = 0;
    const interval = setInterval(() => {
      if (lineIndex < codeLines.length) {
        setLines((prev) => [...prev, codeLines[lineIndex]]);
        lineIndex++;
      } else {
        clearInterval(interval);
      }
    }, 800);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-full max-w-2xl">
      <div className="glass-effect rounded-lg p-6 font-mono text-sm">
        {/* Terminal Header */}
        <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/10">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="ml-2 text-gray-400">terminal</span>
        </div>

        {/* Terminal Content */}
        <div className="space-y-2">
          {lines.map((line, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              className={
                line.startsWith('$')
                  ? 'text-cyan-400'
                  : line.startsWith('✓')
                  ? 'text-green-400'
                  : line.startsWith('>')
                  ? 'text-purple-400'
                  : 'text-gray-300'
              }
            >
              {line}
            </motion.div>
          ))}
          {lines.length === codeLines.length && (
            <motion.span
              className="inline-block w-2 h-4 bg-cyan-400"
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.8, repeat: Infinity }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
