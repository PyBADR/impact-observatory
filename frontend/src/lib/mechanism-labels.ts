/**
 * Bilingual human-readable labels for transmission / propagation mechanism keys.
 *
 * The pipeline emits internal keys (e.g. `price_transmission`, `claims_cascade`)
 * that describe HOW stress transfers between entities. Those keys must never be
 * rendered raw to an executive audience — this module maps each key to an
 * English and Arabic business-safe label.
 *
 * Coverage:
 *   - Macro propagation mechanisms emitted by risk_models.py + explainability_engine.py
 *     (direct_shock, price_transmission, physical_constraint, capacity_overflow,
 *     supply_chain, claims_cascade, monetary_transmission, propagation,
 *     initial_shock, sector_accumulation, decision_trigger, severity_threshold_rule)
 *   - Banking TransferMechanism enum values
 *     (liquidity_channel, credit_channel, payment_channel, confidence_channel,
 *     operational_channel, regulatory_channel, market_channel, contagion)
 *
 * Fallback: if the backend emits a key not in the map, `mechanismLabel`
 * sentence-cases the underscored key (e.g. `foo_bar_baz` → `Foo Bar Baz`)
 * so a previously unseen key still renders cleanly instead of raw.
 */

export interface MechanismLabel {
  en: string;
  ar: string;
}

const MECHANISM_LABEL_MAP: Record<string, MechanismLabel> = {
  // ── Macro propagation mechanisms ─────────────────────────────────
  direct_shock: {
    en: "Direct Shock",
    ar: "صدمة مباشرة",
  },
  initial_shock: {
    en: "Initial Shock",
    ar: "الصدمة الأولية",
  },
  price_transmission: {
    en: "Price Transmission",
    ar: "انتقال الأسعار",
  },
  physical_constraint: {
    en: "Physical Constraint",
    ar: "قيد مادي",
  },
  capacity_overflow: {
    en: "Capacity Overflow",
    ar: "تجاوز الطاقة الاستيعابية",
  },
  supply_chain: {
    en: "Supply Chain",
    ar: "سلسلة الإمداد",
  },
  claims_cascade: {
    en: "Claims Cascade",
    ar: "تتابع المطالبات",
  },
  monetary_transmission: {
    en: "Monetary Transmission",
    ar: "الانتقال النقدي",
  },
  propagation: {
    en: "Propagation",
    ar: "الانتشار",
  },
  sector_accumulation: {
    en: "Sector Accumulation",
    ar: "تراكم قطاعي",
  },
  decision_trigger: {
    en: "Decision Trigger",
    ar: "محفز القرار",
  },
  severity_threshold_rule: {
    en: "Severity Threshold",
    ar: "عتبة الحدة",
  },

  // ── Banking TransferMechanism enum ───────────────────────────────
  liquidity_channel: {
    en: "Liquidity Channel",
    ar: "قناة السيولة",
  },
  credit_channel: {
    en: "Credit Channel",
    ar: "قناة الائتمان",
  },
  payment_channel: {
    en: "Payments Channel",
    ar: "قناة المدفوعات",
  },
  confidence_channel: {
    en: "Confidence Channel",
    ar: "قناة الثقة",
  },
  operational_channel: {
    en: "Operational Channel",
    ar: "القناة التشغيلية",
  },
  regulatory_channel: {
    en: "Regulatory Channel",
    ar: "القناة التنظيمية",
  },
  market_channel: {
    en: "Market Channel",
    ar: "قناة السوق",
  },
  contagion: {
    en: "Contagion",
    ar: "عدوى مالية",
  },
};

/**
 * Sentence-case an underscored key as a safe fallback.
 *   foo_bar_baz → Foo Bar Baz
 *   price_transmission → Price Transmission
 */
function humanizeKey(key: string): string {
  if (!key) return "";
  return key
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

/**
 * Return a bilingual label pair for a mechanism key. Unknown keys fall back
 * to a sentence-cased humanisation so raw underscore keys never leak to the UI.
 */
export function mechanismLabel(
  key: string | null | undefined,
): MechanismLabel {
  const normalized = (key ?? "").toString().trim().toLowerCase();
  if (!normalized) {
    return { en: "Propagation", ar: "الانتشار" };
  }
  const hit = MECHANISM_LABEL_MAP[normalized];
  if (hit) return hit;
  const humanized = humanizeKey(normalized);
  return { en: humanized, ar: humanized };
}

/**
 * Convenience helper — pick the right side of the bilingual pair for the
 * active locale. Defaults to English when `locale` is undefined.
 */
export function mechanismLabelFor(
  key: string | null | undefined,
  locale: "en" | "ar" = "en",
): string {
  const pair = mechanismLabel(key);
  return locale === "ar" ? pair.ar : pair.en;
}
