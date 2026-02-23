'use client'

import { signOut } from '@/app/actions/auth'

export function LogoutButton() {
  return (
    <form action={signOut}>
      <button
        type="submit"
        className="text-sm text-zinc-400 hover:text-white transition-colors px-3 py-1.5 rounded-md hover:bg-zinc-800"
      >
        Sign Out
      </button>
    </form>
  )
}
