export default function HeroSection() {
  return (
    <header className="relative px-6 pt-6 pb-2">
      <nav className="relative mx-auto flex max-w-5xl items-center justify-between rounded-2xl glass px-6 py-3">
        <span className="text-lg font-bold tracking-tight text-white">
          <span className="text-cyan-400">Agency</span>OS
        </span>
        <div className="flex items-center gap-6 text-sm text-slate-400">
          <a href="#features" className="transition-colors hover:text-white">Tính năng</a>
          <a href="#cascade" className="transition-colors hover:text-white">Cascade</a>
          <a href="#pricing" className="transition-colors hover:text-white">Giá</a>
          <a
            href="https://github.com/agencyos/mekong-cli"
            className="transition-colors hover:text-white"
          >
            GitHub
          </a>
          <a
            href="#quickstart"
            className="rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-500"
          >
            Bắt đầu
          </a>
        </div>
      </nav>
    </header>
  )
}
