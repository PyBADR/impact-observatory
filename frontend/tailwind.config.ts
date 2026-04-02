import type { Config } from "tailwindcss";

/**
 * Impact Observatory | مرصد الأثر — Design System Tokens
 *
 * theme:
 *   mode: light
 *   design_rules: clean_spacing, premium_cards, no_neon, no_black_default,
 *                 boardroom_aesthetic, graph_is_secondary
 */
const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Canonical palette from project spec
        io: {
          bg:         '#F8FAFC',
          surface:    '#FFFFFF',
          primary:    '#0F172A',
          secondary:  '#475569',
          accent:     '#1D4ED8',
          success:    '#15803D',
          warning:    '#B45309',
          danger:     '#B91C1C',
          border:     '#E2E8F0',
        },
        // Design system tokens (ds-* for backward compatibility)
        ds: {
          bg: '#F8FAFC', 'bg-alt': '#F1F5F9', surface: '#FFFFFF', 'surface-raised': '#FFFFFF',
          card: '#FFFFFF', 'card-hover': '#F8FAFC', 'card-active': '#F1F5F9',
          border: '#E2E8F0', 'border-subtle': '#F1F5F9', 'border-accent': '#CBD5E1', 'border-hover': '#94A3B8',
          text: '#0F172A', 'text-secondary': '#475569', 'text-muted': '#94A3B8', 'text-dim': '#CBD5E1',
          accent: '#1D4ED8', 'accent-hover': '#1E40AF', 'accent-dim': '#3B82F6',
          'accent-muted': 'rgba(29, 78, 216, 0.06)', 'accent-glow': 'rgba(29, 78, 216, 0.04)',
          gold: '#B45309', 'gold-light': '#D97706', 'gold-muted': 'rgba(180, 83, 9, 0.08)',
          success: '#15803D', 'success-dim': 'rgba(21, 128, 61, 0.06)',
          warning: '#B45309', 'warning-dim': 'rgba(180, 83, 9, 0.06)',
          danger: '#B91C1C', 'danger-dim': 'rgba(185, 28, 28, 0.06)',
          critical: '#7F1D1D', 'critical-dim': 'rgba(127, 29, 29, 0.05)',
        },
      },
      fontFamily: {
        en: ['DM Sans', 'system-ui', 'sans-serif'],
        ar: ['IBM Plex Sans Arabic', 'Noto Sans Arabic', 'sans-serif'],
        sans: ['DM Sans', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'display': ['4rem', { lineHeight: '1.06', letterSpacing: '-0.03em', fontWeight: '700' }],
        'display-sm': ['3rem', { lineHeight: '1.08', letterSpacing: '-0.025em', fontWeight: '700' }],
        'h1': ['2.25rem', { lineHeight: '1.12', letterSpacing: '-0.02em', fontWeight: '700' }],
        'h2': ['1.75rem', { lineHeight: '1.18', letterSpacing: '-0.015em', fontWeight: '600' }],
        'h3': ['1.25rem', { lineHeight: '1.3', letterSpacing: '-0.01em', fontWeight: '600' }],
        'h4': ['1.0625rem', { lineHeight: '1.4', letterSpacing: '-0.005em', fontWeight: '600' }],
        'body-lg': ['1.0625rem', { lineHeight: '1.7' }],
        'body': ['0.9375rem', { lineHeight: '1.65' }],
        'caption': ['0.8125rem', { lineHeight: '1.55' }],
        'micro': ['0.75rem', { lineHeight: '1.5' }],
        'nano': ['0.6875rem', { lineHeight: '1.45' }],
      },
      borderRadius: { 'ds': '8px', 'ds-lg': '12px', 'ds-xl': '16px', 'ds-2xl': '20px' },
      boxShadow: {
        // Premium card shadows — boardroom aesthetic, no neon
        'ds': '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)',
        'ds-md': '0 4px 6px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.06)',
        'ds-lg': '0 10px 15px rgba(0,0,0,0.04), 0 4px 6px rgba(0,0,0,0.05)',
        'ds-glow': '0 0 0 1px rgba(29, 78, 216, 0.06)',
        'ds-glow-md': '0 0 0 1px rgba(29, 78, 216, 0.10)',
        'ds-glow-accent': '0 0 0 3px rgba(29, 78, 216, 0.06)',
        'ds-inner': 'inset 0 1px 0 rgba(255,255,255,0.6)',
        'ds-card-hover': '0 8px 25px rgba(0,0,0,0.05), 0 0 0 1px rgba(29, 78, 216, 0.04)',
      },
      spacing: { '18': '4.5rem', '22': '5.5rem', '26': '6.5rem', '30': '7.5rem', '34': '8.5rem', '38': '9.5rem' },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-soft': 'pulseSoft 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(16px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        pulseSoft: { '0%, 100%': { opacity: '0.5' }, '50%': { opacity: '0.8' } },
      },
    },
  },
  plugins: [],
};
export default config;
