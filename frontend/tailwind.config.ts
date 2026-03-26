import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        ds: {
          bg: '#06060A', 'bg-alt': '#09090E', surface: '#0E0E14', 'surface-raised': '#121218',
          card: '#14141C', 'card-hover': '#191922', 'card-active': '#1E1E2A',
          border: '#1C1C2A', 'border-subtle': '#16161F', 'border-accent': '#262640', 'border-hover': '#2A2A42',
          text: '#F0F0F4', 'text-secondary': '#8A8AA2', 'text-muted': '#5A5A70', 'text-dim': '#3A3A4E',
          accent: '#5B7BF8', 'accent-hover': '#4C6AE8', 'accent-dim': '#3D55B8',
          'accent-muted': 'rgba(91, 123, 248, 0.10)', 'accent-glow': 'rgba(91, 123, 248, 0.05)',
          success: '#2DD4A0', 'success-dim': 'rgba(45, 212, 160, 0.10)',
          warning: '#F5A623', 'warning-dim': 'rgba(245, 166, 35, 0.10)',
          danger: '#EF5454', 'danger-dim': 'rgba(239, 84, 84, 0.10)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'display': ['5.5rem', { lineHeight: '1.02', letterSpacing: '-0.04em', fontWeight: '700' }],
        'display-sm': ['4rem', { lineHeight: '1.04', letterSpacing: '-0.035em', fontWeight: '700' }],
        'h1': ['3rem', { lineHeight: '1.08', letterSpacing: '-0.03em', fontWeight: '700' }],
        'h2': ['2.25rem', { lineHeight: '1.12', letterSpacing: '-0.025em', fontWeight: '600' }],
        'h3': ['1.5rem', { lineHeight: '1.25', letterSpacing: '-0.02em', fontWeight: '600' }],
        'h4': ['1.125rem', { lineHeight: '1.35', letterSpacing: '-0.01em', fontWeight: '600' }],
        'body-lg': ['1.125rem', { lineHeight: '1.75' }],
        'body': ['1rem', { lineHeight: '1.7' }],
        'caption': ['0.875rem', { lineHeight: '1.6' }],
        'micro': ['0.75rem', { lineHeight: '1.5' }],
        'nano': ['0.6875rem', { lineHeight: '1.45' }],
      },
      borderRadius: { 'ds': '10px', 'ds-lg': '14px', 'ds-xl': '20px', 'ds-2xl': '24px' },
      boxShadow: {
        'ds': '0 1px 2px rgba(0,0,0,0.5), 0 4px 16px rgba(0,0,0,0.25)',
        'ds-md': '0 2px 8px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.3)',
        'ds-lg': '0 4px 16px rgba(0,0,0,0.5), 0 16px 48px rgba(0,0,0,0.35)',
        'ds-glow': '0 0 40px rgba(91, 123, 248, 0.05)',
        'ds-glow-md': '0 0 60px rgba(91, 123, 248, 0.08)',
        'ds-glow-accent': '0 0 20px rgba(91, 123, 248, 0.15), 0 0 60px rgba(91, 123, 248, 0.05)',
        'ds-inner': 'inset 0 1px 0 rgba(255,255,255,0.03)',
        'ds-card-hover': '0 4px 20px rgba(0,0,0,0.4), 0 0 40px rgba(91, 123, 248, 0.03)',
      },
      spacing: { '18': '4.5rem', '22': '5.5rem', '26': '6.5rem', '30': '7.5rem', '34': '8.5rem', '38': '9.5rem' },
      animation: {
        'fade-in': 'fadeIn 0.7s ease-out forwards',
        'slide-up': 'slideUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-soft': 'pulseSoft 3s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(24px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        pulseSoft: { '0%, 100%': { opacity: '0.4' }, '50%': { opacity: '0.7' } },
        pulseGlow: { '0%, 100%': { opacity: '0.4' }, '50%': { opacity: '0.85' } },
        float: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } },
      },
    },
  },
  plugins: [],
}
export default config
