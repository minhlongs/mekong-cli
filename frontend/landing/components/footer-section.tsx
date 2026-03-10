const LAYER_LINKS = [
  { label: '👑 Founder', href: '/founder' },
  { label: '🏢 Business', href: '/business' },
  { label: '📦 Product', href: '/product' },
  { label: '⚙️ Dev', href: '/dev/quickstart' },
  { label: '🔧 Ops', href: '/ops' },
  { label: '💰 Pricing', href: '/pricing' },
]

const EXTERNAL_LINKS = [
  { label: 'GitHub', href: 'https://github.com/agencyos/mekong-cli' },
  { label: 'Docs', href: 'https://docs.agencyos.network' },
  { label: 'Discord', href: 'https://discord.gg/agencyos' },
  { label: 'Terms', href: '/terms' },
  { label: 'Privacy', href: '/privacy' },
]

export default function FooterSection() {
  return (
    <footer className="border-t border-slate-900 px-6 py-12">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 grid gap-8 sm:grid-cols-3">
          {/* Brand */}
          <div>
            <div className="mb-1 text-lg font-bold text-white">
              <span className="text-cyan-400">Agency</span>OS
            </div>
            <p className="mb-3 text-xs text-slate-600">AGI Vibe Coding Factory</p>
            <a
              href="https://github.com/agencyos/mekong-cli"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              Powered by Mekong CLI
            </a>
          </div>

          {/* Layers */}
          <nav>
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">Layers</p>
            <div className="flex flex-col gap-2">
              {LAYER_LINKS.map((l) => (
                <a
                  key={l.href}
                  href={l.href}
                  className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {l.label}
                </a>
              ))}
            </div>
          </nav>

          {/* Links */}
          <nav>
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">Links</p>
            <div className="flex flex-col gap-2">
              {EXTERNAL_LINKS.map((l) => (
                <a
                  key={l.label}
                  href={l.href}
                  className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {l.label}
                </a>
              ))}
            </div>
          </nav>
        </div>

        <div className="border-t border-slate-900 pt-8 text-center text-xs text-slate-700">
          <p>© 2026 Binh Pháp Venture Studio. All rights reserved.</p>
          <p className="mt-1 font-mono">
            孫子兵法 · Plan → Execute → Verify · Built with Mekong CLI
          </p>
        </div>
      </div>
    </footer>
  )
}
