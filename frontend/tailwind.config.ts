import type { Config } from "tailwindcss";

/**
 * Impact Observatory | مرصد الأثر — Tailwind Design Tokens
 *
 * Calm, institutional, Apple-inspired.
 * Neutral light palette. No neon. No blue-led. No admin-panel aesthetics.
 */
const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        io: {
          // Surfaces
          bg:          '#F5F5F2',
          surface:     '#FFFFFF',
          muted:       '#ECECE8',
          // Text
          primary:     '#111111',
          secondary:   '#5F5F58',
          tertiary:    '#8A8A83',
          // Borders
          'border-soft':  '#D9D9D2',
          'border-muted': '#E6E6E0',
          // Emphasis
          charcoal:    '#1B1B19',
          graphite:    '#252522',
          // Status (muted, institutional)
          'status-amber': '#A06A34',
          'status-red':   '#8E4338',
          'status-olive': '#5E6759',
        },
        // Legacy ds-* tokens preserved for backward compatibility
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
        sans: ['DM Sans', 'system-ui', '-apple-system', 'sans-serif'],
        ar:   ['IBM Plex Sans Arabic', 'Noto Sans Arabic', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'hero':       ['4rem',     { lineHeight: '1.06', letterSpacing: '-0.03em', fontWeight: '700' }],
        'hero-sm':    ['3rem',     { lineHeight: '1.08', letterSpacing: '-0.025em', fontWeight: '700' }],
        'heading-1':  ['2.5rem',   { lineHeight: '1.1',  letterSpacing: '-0.025em', fontWeight: '700' }],
        'heading-2':  ['1.75rem',  { lineHeight: '1.2',  letterSpacing: '-0.02em',  fontWeight: '600' }],
        'heading-3':  ['1.25rem',  { lineHeight: '1.35', letterSpacing: '-0.01em',  fontWeight: '600' }],
        'body-lg':    ['1.0625rem',{ lineHeight: '1.7' }],
        'body':       ['0.9375rem',{ lineHeight: '1.65' }],
        'caption':    ['0.875rem', { lineHeight: '1.5' }],
        'label':      ['0.75rem',  { lineHeight: '1.4',  letterSpacing: '0.04em',  fontWeight: '600' }],
        'micro':      ['0.6875rem',{ lineHeight: '1.45' }],
      },
      borderRadius: {
        'card': '12px',
        'badge': '6px',
      },
      boxShadow: {
        'quiet':       '0 1px 3px rgba(0,0,0,0.03)',
        'quiet-md':    '0 2px 8px rgba(0,0,0,0.04)',
        'quiet-lg':    '0 4px 16px rgba(0,0,0,0.05)',
        // Legacy shadows preserved
        'ds':          '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)',
        'ds-md':       '0 4px 6px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.06)',
        'ds-lg':       '0 10px 15px rgba(0,0,0,0.04), 0 4px 6px rgba(0,0,0,0.05)',
        'ds-card-hover':'0 8px 25px rgba(0,0,0,0.05), 0 0 0 1px rgba(29, 78, 216, 0.04)',
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '26': '6.5rem',
        '30': '7.5rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
