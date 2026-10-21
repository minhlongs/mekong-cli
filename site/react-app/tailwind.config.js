/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'obsidian-bg': '#090A0F',
        'slate-panel': '#11131A',
        'slate-hover': '#181B26',
        'border-subtle': '#1E2230',
        'border-active': '#2D3748',
        'cyber-emerald': '#10B981',
        'electric-cyan': '#06B6D4',
        'warning-amber': '#F59E0B',
        'danger-crimson': '#EF4444',
      },
      fontFamily: {
        heading: ['Space Grotesk', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'card': '12px',
        'btn': '8px',
      }
    },
  },
  plugins: [],
}
