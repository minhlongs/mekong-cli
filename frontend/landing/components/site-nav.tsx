const NAV_LINKS = [
  { label: '👑 Founder', href: '/founder' },
  { label: '🏢 Business', href: '/business' },
  { label: '📦 Product', href: '/product' },
  { label: '⚙️ Dev', href: '/dev/quickstart' },
  { label: '🔧 Ops', href: '/ops' },
  { label: '💰 Pricing', href: '/pricing' },
]

export default function SiteNav() {
  return (
    <header className="relative px-6 pt-6 pb-2">
      <nav className="relative mx-auto flex max-w-5xl items-center justify-between rounded-2xl glass px-6 py-3">
        {/* Logo */}
        <a href="/" className="text-lg font-bold tracking-tight text-white hover:opacity-80 transition-opacity">
          <span className="text-cyan-400">Agency</span>OS
        </a>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-5 text-sm text-slate-400">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="transition-colors hover:text-white"
            >
              {link.label}
            </a>
          ))}
          <a
            href="https://github.com/agencyos/mekong-cli"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-white"
            aria-label="GitHub"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
          </a>
          <a
            href="#quickstart"
            className="rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-500"
          >
            Bắt đầu
          </a>
        </div>

        {/* Mobile hamburger via details/summary — no JS */}
        <details className="md:hidden group">
          <summary className="cursor-pointer list-none rounded-lg p-2 text-slate-400 hover:text-white transition-colors">
            <svg className="h-5 w-5 group-open:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <svg className="hidden h-5 w-5 group-open:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </summary>
          <div className="absolute left-6 right-6 top-full mt-2 rounded-2xl glass p-4 z-50">
            <div className="flex flex-col gap-3 text-sm text-slate-300">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="rounded-lg px-3 py-2 transition-colors hover:bg-slate-800 hover:text-white"
                >
                  {link.label}
                </a>
              ))}
              <a
                href="https://github.com/agencyos/mekong-cli"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg px-3 py-2 transition-colors hover:bg-slate-800 hover:text-white"
              >
                GitHub
              </a>
            </div>
          </div>
        </details>
      </nav>
    </header>
  )
}
