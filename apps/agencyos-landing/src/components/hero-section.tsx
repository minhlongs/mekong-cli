import Link from "next/link";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden pt-16 md:pt-24 lg:pt-32 pb-16">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-700 ring-1 ring-inset ring-indigo-700/10 mb-8 dark:bg-indigo-950/30 dark:text-indigo-400 dark:ring-indigo-400/20">
          <span className="flex h-2 w-2 rounded-full bg-indigo-600 dark:bg-indigo-400 animate-pulse"></span>
          v1.0.0 Now Available
        </div>

        <h1 className="mx-auto max-w-4xl text-5xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-7xl mb-6">
          The Operating System for <br className="hidden sm:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600 dark:from-indigo-400 dark:to-violet-400">
            Modern Agencies
          </span>
        </h1>

        <p className="mx-auto max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-400 mb-10">
          Scale your agency with AI-powered RaaS (Result-as-a-Service).
          Automate workflows, track growth metrics, and deploy viral recipes with the Mekong CLI.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="#pricing"
            className="w-full sm:w-auto inline-flex h-12 items-center justify-center rounded-md bg-indigo-600 px-8 text-base font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-slate-950"
          >
            Get Started - $99
          </Link>
          <Link
            href="https://github.com/agencyos/mekong-cli"
            target="_blank"
            className="w-full sm:w-auto inline-flex h-12 items-center justify-center rounded-md border border-slate-200 bg-white px-8 text-base font-semibold text-slate-900 shadow-sm transition-colors hover:bg-slate-50 hover:text-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-900"
          >
            npm install -g mekong
          </Link>
        </div>

        <div className="mt-16 relative mx-auto max-w-5xl">
          <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 opacity-30 blur-lg dark:opacity-40"></div>
          <div className="relative rounded-xl bg-slate-900/5 p-2 ring-1 ring-inset ring-slate-900/10 dark:bg-slate-100/5 dark:ring-white/10 lg:rounded-2xl lg:p-4">
             <div className="rounded-md bg-slate-900 shadow-2xl overflow-hidden border border-slate-800">
                <div className="flex items-center gap-2 bg-slate-800/50 px-4 py-3 border-b border-slate-800">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  </div>
                  <div className="text-xs text-slate-400 font-mono ml-2">mekong-cli — v1.0.0</div>
                </div>
                <div className="p-6 font-mono text-sm text-slate-300 text-left overflow-x-auto">
                  <div className="flex mb-2">
                    <span className="text-indigo-400 mr-2">➜</span>
                    <span className="text-white">mekong init</span>
                  </div>
                  <div className="mb-4 text-slate-400">
                    Initializing AgencyOS environment...<br/>
                    ✅ Architecture detected: Next.js + Supabase<br/>
                    ✅ Binh Phap modules loaded: 6/6<br/>
                    ✅ Telemetry engine: @agencyos/vibe-analytics connected<br/>
                    <br/>
                    <span className="text-green-400">AgencyOS initialized successfully! 🚀</span>
                  </div>
                  <div className="flex mb-2">
                     <span className="text-indigo-400 mr-2">➜</span>
                     <span className="text-white">mekong recipe install viral-loop</span>
                  </div>
                   <div className="mb-4 text-slate-400">
                    📦 Downloading viral-loop recipe...<br/>
                    ⚙️ Configuring referral system...<br/>
                    ✨ Recipe installed!
                  </div>
                </div>
             </div>
          </div>
        </div>
      </div>

      {/* Background gradients */}
      <div className="absolute top-0 left-1/2 -z-10 -translate-x-1/2 transform-gpu blur-3xl" aria-hidden="true">
        <div className="aspect-[1155/678] w-[68.5625rem] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-20" style={{ clipPath: "polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)" }}></div>
      </div>
    </section>
  );
}
