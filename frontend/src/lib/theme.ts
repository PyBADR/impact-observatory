/**
 * Impact Observatory | مرصد الأثر — Design Tokens
 *
 * Single source of truth for the calm, institutional palette.
 * Components that need programmatic token access import from here.
 * CSS variables live in globals.css — these are the JS mirrors.
 */

export const colors = {
  bg: {
    main:    '#F5F5F2',
    surface: '#FFFFFF',
    muted:   '#ECECE8',
  },
  text: {
    primary:   '#111111',
    secondary: '#5F5F58',
    tertiary:  '#8A8A83',
  },
  border: {
    soft:  '#D9D9D2',
    muted: '#E6E6E0',
  },
  emphasis: {
    charcoal: '#1B1B19',
    graphite: '#252522',
  },
  status: {
    amber: '#A06A34',
    red:   '#8E4338',
    olive: '#5E6759',
  },
} as const;

export const typography = {
  hero: {
    fontSize: '3.5rem',
    lineHeight: 1.06,
    letterSpacing: '-0.03em',
    fontWeight: 700,
  },
  heading1: {
    fontSize: '2.5rem',
    lineHeight: 1.1,
    letterSpacing: '-0.025em',
    fontWeight: 700,
  },
  heading2: {
    fontSize: '1.75rem',
    lineHeight: 1.2,
    letterSpacing: '-0.02em',
    fontWeight: 600,
  },
  heading3: {
    fontSize: '1.25rem',
    lineHeight: 1.35,
    letterSpacing: '-0.01em',
    fontWeight: 600,
  },
  body: {
    fontSize: '1.0625rem',
    lineHeight: 1.7,
    fontWeight: 400,
  },
  caption: {
    fontSize: '0.875rem',
    lineHeight: 1.5,
    fontWeight: 500,
  },
  label: {
    fontSize: '0.75rem',
    lineHeight: 1.4,
    fontWeight: 600,
    letterSpacing: '0.04em',
    textTransform: 'uppercase' as const,
  },
} as const;

export const spacing = {
  section:   '6rem',
  sectionMd: '4rem',
  block:     '2.5rem',
  element:   '1.5rem',
  tight:     '0.75rem',
} as const;

export const radii = {
  card:  '12px',
  badge: '6px',
  pill:  '999px',
} as const;

/** Risk severity levels mapped to the URS thresholds in the backend. */
export type StatusLevel = 'nominal' | 'low' | 'guarded' | 'elevated' | 'high' | 'severe';

export const statusColors: Record<StatusLevel, { bg: string; text: string; border: string }> = {
  nominal:  { bg: '#F0F0ED', text: '#5E6759', border: '#D9D9D2' },
  low:      { bg: '#F0F0ED', text: '#5E6759', border: '#D9D9D2' },
  guarded:  { bg: '#F5F0E6', text: '#A06A34', border: '#E6DCC8' },
  elevated: { bg: '#F5F0E6', text: '#A06A34', border: '#E6DCC8' },
  high:     { bg: '#F2E8E6', text: '#8E4338', border: '#E0CCC8' },
  severe:   { bg: '#F2E8E6', text: '#8E4338', border: '#E0CCC8' },
};
