import Image from "next/image";

export default function Home() {
  return (
    <div className="min-h-screen bg-black text-zinc-50 selection:bg-zinc-800 selection:text-zinc-100 font-sans">
      {/* Navigation */}
      <nav className="fixed top-0 z-50 w-full border-b border-white/5 bg-black/50 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-zinc-100" />
            <span className="text-xl font-bold tracking-tight">mekong-cli</span>
          </div>
          <div className="hidden gap-8 text-sm font-medium text-zinc-400 md:flex">
            <a href="#features" className="hover:text-zinc-50 transition-colors">Features</a>
            <a href="#pricing" className="hover:text-zinc-50 transition-colors">Pricing</a>
            <a href="https://github.com/mekong-cli/mekong-cli" className="hover:text-zinc-50 transition-colors">GitHub</a>
          </div>
          <a
            href="https://github.com/mekong-cli/mekong-cli"
            className="rounded-full bg-zinc-100 px-4 py-2 text-sm font-semibold text-black hover:bg-zinc-300 transition-colors"
          >
            Get Started
          </a>
        </div>
      </nav>

      <main className="pt-20">
        {/* Hero Section */}
        <section className="relative flex flex-col items-center justify-center overflow-hidden py-24 md:py-32">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(45%_45%_at_50%_50%,#1a1a1a_0%,#000_100%)]" />
          <div className="container mx-auto px-6 text-center">
            <h1 className="animate-in fade-in slide-in-from-bottom-4 duration-1000 bg-gradient-to-b from-white to-zinc-500 bg-clip-text text-5xl font-black tracking-tight text-transparent sm:text-7xl md:text-8xl">
              mekong-cli
            </h1>
            <p className="animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-150 mx-auto mt-6 max-w-2xl text-xl font-medium text-zinc-400 md:text-2xl">
              AGI Vibe Coding Engine — The Agentic OS for autonomous coding.
            </p>
            <div className="animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-300 mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <a
                href="https://github.com/mekong-cli/mekong-cli"
                className="group flex h-14 w-full items-center justify-center gap-2 rounded-xl bg-zinc-100 px-8 text-lg font-bold text-black hover:bg-zinc-300 transition-all sm:w-auto"
              >
                View on GitHub
                <svg className="h-5 w-5 transition-transform group-hover:translate-x-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14m-7-7 7 7-7 7" />
                </svg>
              </a>
              <button className="h-14 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-8 text-lg font-bold text-zinc-100 hover:bg-zinc-900 transition-all sm:w-auto">
                Documentation
              </button>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24 border-t border-white/5 bg-zinc-950/50">
          <div className="container mx-auto px-6">
            <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
              <div className="group rounded-2xl border border-white/5 bg-zinc-900/50 p-8 hover:border-white/10 transition-colors">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-100 text-black">
                  <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v20m10-10H2" />
                  </svg>
                </div>
                <h3 className="mb-3 text-xl font-bold">Auto-CTO</h3>
                <p className="text-zinc-400 leading-relaxed">
                  Autonomous quality control & strategic planning. Tôm Hùm daemon watches your projects 24/7.
                </p>
              </div>
              <div className="group rounded-2xl border border-white/5 bg-zinc-900/50 p-8 hover:border-white/10 transition-colors">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-100 text-black">
                  <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 7h-9m3 3H5m11 3h-5m3 3H5" />
                  </svg>
                </div>
                <h3 className="mb-3 text-xl font-bold">Binh Pháp AI</h3>
                <p className="text-zinc-400 leading-relaxed">
                  Sun Tzu's Art of War applied to software delivery. Systematic execution with 10x efficiency.
                </p>
              </div>
              <div className="group rounded-2xl border border-white/5 bg-zinc-900/50 p-8 hover:border-white/10 transition-colors">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-100 text-black">
                  <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 1v22M5 12h14" />
                  </svg>
                </div>
                <h3 className="mb-3 text-xl font-bold">Free Open Source</h3>
                <p className="text-zinc-400 leading-relaxed">
                  Community-driven, transparent core. Built by developers for developers. Apache 2.0.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-24 border-t border-white/5">
          <div className="container mx-auto px-6">
            <div className="mb-16 text-center">
              <h2 className="text-4xl font-bold tracking-tight">Simple Pricing</h2>
              <p className="mt-4 text-zinc-400">Choose the best way to run your mekong agents.</p>
            </div>
            <div className="mx-auto grid max-w-4xl grid-cols-1 gap-8 md:grid-cols-2">
              <div className="flex flex-col rounded-3xl border border-white/5 bg-zinc-900/50 p-8">
                <h3 className="text-xl font-bold">Free Open Source</h3>
                <div className="mt-4 flex items-baseline gap-1">
                  <span className="text-4xl font-black">$0</span>
                  <span className="text-zinc-400">/forever</span>
                </div>
                <p className="mt-4 text-sm text-zinc-400">Perfect for individuals and local dev.</p>
                <ul className="mt-8 space-y-4 text-sm font-medium">
                  <li className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                    Self-hosted agents
                  </li>
                  <li className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                    Full source access
                  </li>
                  <li className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                    Unlimited missions
                  </li>
                </ul>
                <button className="mt-10 rounded-xl border border-zinc-800 py-3 font-bold hover:bg-zinc-800 transition-colors">
                  Fork on GitHub
                </button>
              </div>
              <div className="relative flex flex-col rounded-3xl border border-zinc-100 bg-zinc-100 p-8 text-black shadow-2xl shadow-zinc-100/10">
                <div className="absolute -top-4 left-8 rounded-full bg-zinc-950 px-4 py-1 text-xs font-black uppercase tracking-widest text-white">
                  Recommended
                </div>
                <h3 className="text-xl font-bold">RaaS Managed</h3>
                <div className="mt-4 flex items-baseline gap-1 text-black">
                  <span className="text-4xl font-black">$99</span>
                  <span className="text-zinc-600 font-bold">/mo</span>
                </div>
                <p className="mt-4 text-sm text-zinc-600">Robot-as-a-Service for enterprises.</p>
                <ul className="mt-8 space-y-4 text-sm font-bold">
                  <li className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-black" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                    Managed Cloud Infra
                  </li>
                  <li className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-black" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                    Premium Model Access
                  </li>
                  <li className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-black" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                    24/7 Priority Support
                  </li>
                </ul>
                <button className="mt-10 rounded-xl bg-zinc-950 py-3 font-bold text-white hover:bg-zinc-800 transition-colors shadow-lg">
                  Subscribe Now
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 bg-black">
        <div className="container mx-auto px-6 text-center text-sm text-zinc-500">
          <p>© 2026 mekong-cli. Built with Advanced Agentic Coding.</p>
        </div>
      </footer>
    </div>
  );
}
