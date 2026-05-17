/** @type {import('tailwindcss').Config} */
// Landing palette — mirrors apps/dashboard/styles/tokens/claude-design.css
// so the dashboard and the marketing site read as one product.
module.exports = {
  content: ['./template.html', './dist/**/*.html'],
  theme: {
    extend: {
      colors: {
        // page surfaces (cream / paper)
        bg: '#faf9f5',         // cream — body background
        surface: '#f5f1e8',     // raised section bands
        paper: '#ffffff',       // cards
        // ink scale
        ink: '#1f1f1c',         // primary text
        body: '#2c2b27',        // alt body text
        ash: '#6b6a64',         // secondary
        muted: '#8a8983',       // tertiary
        // borders
        border: '#e8e1d4',
        'border-strong': '#d8cfbe',
        // brand
        accent: 'var(--accent-color, #d97757)',   // Claude clay
        'accent-deep': '#c96342',
        'accent-soft': '#efbb9e',
        cta: '#d97757',
        // status
        success: '#2c8a5b',
        warn: '#c97a1a',
        danger: '#b1483a',
        // legacy aliases — keep templates that still reference these
        text: '#1f1f1c',
      },
      fontFamily: {
        sans: [
          'Söhne', 'Söhne Buch', 'Inter',
          '-apple-system', 'BlinkMacSystemFont', 'system-ui',
          'Segoe UI', 'Roboto', 'sans-serif',
        ],
        serif: [
          'Tiempos Headline', 'Tiempos Text',
          'Iowan Old Style', 'Apple Garamond', 'Baskerville',
          'Source Serif Pro', 'Georgia', 'serif',
        ],
        mono: [
          'Söhne Mono', 'JetBrains Mono', 'IBM Plex Mono',
          'SF Mono', 'Menlo', 'Consolas', 'monospace',
        ],
      },
      fontSize: {
        '3xs': ['10px', { lineHeight: '1.4' }],
        '2xs': ['11px', { lineHeight: '1.4' }],
        xs:    ['12px', { lineHeight: '1.5' }],
        sm:    ['13.5px', { lineHeight: '1.55' }],
        base:  ['15px', { lineHeight: '1.55' }],
        lg:    ['17px', { lineHeight: '1.6' }],
        xl:    ['21px', { lineHeight: '1.4' }],
        '2xl': ['28px', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
        '3xl': ['38px', { lineHeight: '1.15', letterSpacing: '-0.02em' }],
        '4xl': ['52px', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        '5xl': ['68px', { lineHeight: '1.05', letterSpacing: '-0.025em' }],
      },
      borderRadius: {
        sm: '5px',
        DEFAULT: '8px',
        md: '8px',
        lg: '12px',
        xl: '18px',
        '2xl': '24px',
        full: '9999px',
      },
      boxShadow: {
        xs: '0 1px 0 rgba(31,31,28,0.04)',
        sm: '0 1px 2px rgba(31,31,28,0.05), 0 0 0 1px rgba(31,31,28,0.04)',
        DEFAULT: '0 4px 12px rgba(31,31,28,0.06), 0 0 0 1px rgba(31,31,28,0.05)',
        md: '0 4px 12px rgba(31,31,28,0.06), 0 0 0 1px rgba(31,31,28,0.05)',
        lg: '0 12px 40px rgba(31,31,28,0.08)',
        focus: '0 0 0 3px rgba(217,119,87,0.32)',
      },
      letterSpacing: {
        tight: '-0.02em',
        normal: '0',
        wide: '0.04em',
        loose: '0.12em',
      },
      backgroundImage: {
        'paper-grain':
          'radial-gradient(rgba(31,31,28,0.025) 1px, transparent 1px)',
      },
      backgroundSize: {
        grain: '22px 22px',
      },
    },
  },
  plugins: [],
};
