export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-xl font-semibold">Settings</h1>

      {/* Account section */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-zinc-800">
          <h2 className="text-sm font-medium text-zinc-200">Account</h2>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="block text-xs text-zinc-500 uppercase tracking-wide mb-1.5">
              Email
            </label>
            <input
              type="email"
              defaultValue="user@example.com"
              readOnly
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300 cursor-not-allowed focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs text-zinc-500 uppercase tracking-wide mb-1.5">
              Display Name
            </label>
            <input
              type="text"
              defaultValue=""
              placeholder="Enter display name"
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300 placeholder-zinc-600 focus:outline-none focus:border-purple-600 transition-colors"
            />
          </div>
          <div className="pt-1">
            <button
              type="button"
              className="px-4 py-2 text-sm font-medium bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors"
            >
              Save changes
            </button>
          </div>
        </div>
      </section>

      {/* API Keys section */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-zinc-800">
          <h2 className="text-sm font-medium text-zinc-200">API Keys</h2>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="block text-xs text-zinc-500 uppercase tracking-wide mb-1.5">
              Secret Key
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                defaultValue="sk-****-****-****-****"
                className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-400 font-mono cursor-not-allowed focus:outline-none"
              />
              <button
                type="button"
                className="px-3 py-2 text-sm text-zinc-400 hover:text-white border border-zinc-700 hover:border-zinc-600 rounded-lg transition-colors whitespace-nowrap"
              >
                Regenerate
              </button>
            </div>
            <p className="mt-1.5 text-xs text-zinc-600">
              Keep your API key secret. Never share it publicly.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
