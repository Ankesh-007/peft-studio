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
        // Dark theme colors
        dark: {
          bg: {
            primary: '#0a0a0a',
            secondary: '#111111',
            tertiary: '#1a1a1a',
          },
          border: '#2a2a2a',
          text: {
            primary: '#ffffff',
            secondary: '#a1a1aa',
            tertiary: '#71717a',
            disabled: '#52525b',
          },
        },
        // Accent colors
        accent: {
          primary: '#6366f1',
          success: '#10b981',
          warning: '#f59e0b',
          error: '#ef4444',
          info: '#3b82f6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        display: ['32px', { lineHeight: '1.2', fontWeight: '700' }],
        h1: ['24px', { lineHeight: '1.3', fontWeight: '600' }],
        h2: ['20px', { lineHeight: '1.4', fontWeight: '600' }],
        h3: ['16px', { lineHeight: '1.5', fontWeight: '600' }],
        body: ['14px', { lineHeight: '1.5', fontWeight: '400' }],
        small: ['12px', { lineHeight: '1.5', fontWeight: '400' }],
        tiny: ['11px', { lineHeight: '1.5', fontWeight: '400' }],
      },
      spacing: {
        '4': '4px',
        '8': '8px',
        '12': '12px',
        '16': '16px',
        '20': '20px',
        '24': '24px',
        '32': '32px',
        '40': '40px',
        '48': '48px',
        '64': '64px',
        '80': '80px',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
