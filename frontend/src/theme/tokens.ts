/**
 * Impact Observatory | مرصد الأثر — Design Tokens
 *
 * Boardroom aesthetic. Clean spacing. Premium cards.
 * No neon. No black default. Graph is secondary.
 */

export const theme = {
  mode: "light" as const,

  palette: {
    background: "#F8FAFC",
    surface: "#FFFFFF",
    primary: "#0F172A",
    secondary: "#475569",
    accent: "#1D4ED8",
    success: "#15803D",
    warning: "#B45309",
    danger: "#B91C1C",
    border: "#E2E8F0",
  },

  classification: {
    critical: "#B91C1C",
    elevated: "#B45309",
    moderate: "#CA8A04",
    low: "#15803D",
    nominal: "#059669",
  },

  typography: {
    fontFamily: "Inter, 'Noto Sans Arabic', system-ui, sans-serif",
    fontFamilyAr: "'Noto Sans Arabic', 'Cairo', system-ui, sans-serif",
    headlineLarge: { fontSize: "2rem", fontWeight: 700, lineHeight: 1.2 },
    headlineMedium: { fontSize: "1.5rem", fontWeight: 600, lineHeight: 1.3 },
    headlineSmall: { fontSize: "1.25rem", fontWeight: 600, lineHeight: 1.4 },
    bodyLarge: { fontSize: "1rem", fontWeight: 400, lineHeight: 1.6 },
    bodySmall: { fontSize: "0.875rem", fontWeight: 400, lineHeight: 1.5 },
    label: { fontSize: "0.75rem", fontWeight: 500, lineHeight: 1.4, letterSpacing: "0.04em", textTransform: "uppercase" as const },
    metric: { fontSize: "2.5rem", fontWeight: 700, lineHeight: 1.1, fontVariantNumeric: "tabular-nums" },
  },

  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
    xxl: "3rem",
  },

  borderRadius: {
    sm: "6px",
    md: "8px",
    lg: "12px",
    xl: "16px",
  },

  shadow: {
    sm: "0 1px 2px rgba(0,0,0,0.04)",
    md: "0 1px 3px rgba(0,0,0,0.08)",
    lg: "0 4px 12px rgba(0,0,0,0.08)",
    xl: "0 8px 24px rgba(0,0,0,0.12)",
  },

  designRules: [
    "clean_spacing",
    "premium_cards",
    "no_neon",
    "no_black_default",
    "boardroom_aesthetic",
    "graph_is_secondary",
  ],
} as const;

export type Theme = typeof theme;
export type Classification = keyof typeof theme.classification;
