/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./template.html", "./dist/**/*.html"],
  theme: {
    extend: {
      colors: {
        bg: '#0F172A',
        surface: '#1E293B',
        border: '#334155',
        accent: 'var(--accent-color, #3B82F6)',
        cta: '#2563EB',
        text: '#F1F5F9',
        muted: '#94A3B8',
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
