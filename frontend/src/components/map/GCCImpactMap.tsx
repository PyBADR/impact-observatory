"use client";

import React, { useMemo } from "react";

interface CountryExposureData {
  stressLevel: number;
  lossUsd: number;
  dominantSector: string;
  entities: string[];
}

interface GCCImpactMapProps {
  countryExposures?: Record<string, CountryExposureData>;
  sectorRollups?: Record<string, { stress: number; loss_usd: number }>;
  scenarioLabel?: string;
  locale?: "en" | "ar";
  onCountryClick?: (countryCode: string) => void;
}

// Default country data
const DEFAULT_COUNTRIES: Record<string, { en: string; ar: string; sector: string; entities: string[] }> = {
  SA: {
    en: "Saudi Arabia",
    ar: "السعودية",
    sector: "Energy",
    entities: ["Saudi Aramco", "SAMA", "Tadawul"],
  },
  AE: {
    en: "UAE",
    ar: "الإمارات",
    sector: "Banking",
    entities: ["CBUAE", "DP World", "ADNOC"],
  },
  QA: {
    en: "Qatar",
    ar: "قطر",
    sector: "Energy",
    entities: ["QatarEnergy", "QCB", "Hamad Port"],
  },
  KW: {
    en: "Kuwait",
    ar: "الكويت",
    sector: "Energy",
    entities: ["KPC", "CBK", "KIA"],
  },
  BH: {
    en: "Bahrain",
    ar: "البحرين",
    sector: "Banking",
    entities: ["CBB", "Bahrain Bourse", "BAPCO"],
  },
  OM: {
    en: "Oman",
    ar: "عُمان",
    sector: "Logistics",
    entities: ["Port of Salalah", "CBO", "PDO"],
  },
};

// Country layout positions (SVG coordinates)
const COUNTRY_POSITIONS: Record<
  string,
  { x: number; y: number; width: number; height: number; label: string }
> = {
  KW: { x: 20, y: 40, width: 80, height: 70, label: "Kuwait" },
  SA: { x: 20, y: 130, width: 110, height: 120, label: "Saudi Arabia" },
  BH: { x: 140, y: 70, width: 60, height: 50, label: "Bahrain" },
  QA: { x: 220, y: 70, width: 70, height: 60, label: "Qatar" },
  AE: { x: 310, y: 90, width: 90, height: 100, label: "UAE" },
  OM: { x: 250, y: 200, width: 100, height: 90, label: "Oman" },
};

function getStressColor(stress: number): string {
  if (stress < 0.2) return "#3A7D6C"; // nominal
  if (stress < 0.35) return "#2D6A4F"; // low
  if (stress < 0.5) return "#5E6759"; // guarded
  if (stress < 0.65) return "#8B6914"; // elevated
  if (stress < 0.8) return "#A0522D"; // high
  return "#8C2318"; // severe
}

function formatUsd(amount: number): string {
  if (amount >= 1e9) return `$${(amount / 1e9).toFixed(1)}B`;
  if (amount >= 1e6) return `$${(amount / 1e6).toFixed(1)}M`;
  return `$${(amount / 1e3).toFixed(0)}K`;
}

export function GCCImpactMap({
  countryExposures = {},
  sectorRollups = {},
  scenarioLabel,
  locale = "en",
  onCountryClick,
}: GCCImpactMapProps): React.ReactElement {
  // Build country data with defaults
  const countryData = useMemo(() => {
    return Object.entries(DEFAULT_COUNTRIES).map(([code, defaults]) => {
      const exposure = countryExposures[code] || {
        stressLevel: 0.15,
        lossUsd: 0,
        dominantSector: defaults.sector,
        entities: defaults.entities,
      };

      return {
        code,
        name: locale === "ar" ? defaults.ar : defaults.en,
        stress: exposure.stressLevel,
        loss: exposure.lossUsd,
        sector: exposure.dominantSector || defaults.sector,
        entities: exposure.entities || defaults.entities,
        color: getStressColor(exposure.stressLevel),
      };
    });
  }, [countryExposures, locale]);

  const title = locale === "ar" ? "خريطة الأثر الخليجية" : "GCC Impact Map";

  const isArabic = locale === "ar";
  const textDir = isArabic ? "rtl" : "ltr";

  return (
    <div className="w-full bg-white rounded-lg border border-slate-200 shadow-sm p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">{title}</h2>
        {scenarioLabel && (
          <p className="text-sm text-slate-600">
            {locale === "ar" ? "السيناريو: " : "Scenario: "}
            <span className="text-io-accent font-semibold">{scenarioLabel}</span>
          </p>
        )}
      </div>

      {/* SVG Map Container */}
      <div className="bg-white rounded-lg border border-slate-200 p-4 mb-6 overflow-x-auto" dir={textDir}>
        <svg viewBox="0 0 450 320" className="w-full min-w-[600px] h-auto" xmlns="http://www.w3.org/2000/svg">
          {/* Water/background */}
          <rect width="450" height="320" fill="#F1F5F9" />

          {/* Grid reference lines (subtle) */}
          <g stroke="#CBD5E1" strokeWidth="0.5" opacity="0.3">
            <line x1="0" y1="160" x2="450" y2="160" />
            <line x1="225" y1="0" x2="225" y2="320" />
          </g>

          {/* Country shapes */}
          {countryData.map((country) => {
            const pos = COUNTRY_POSITIONS[country.code];
            if (!pos) return null;

            const stressText = `${(country.stress * 100).toFixed(0)}%`;

            return (
              <g key={country.code}>
                {/* Country box */}
                <rect
                  x={pos.x}
                  y={pos.y}
                  width={pos.width}
                  height={pos.height}
                  rx="6"
                  fill={country.color}
                  opacity="0.2"
                  stroke={country.color}
                  strokeWidth="2"
                  className="cursor-pointer hover:opacity-3 transition-opacity"
                  onClick={() => onCountryClick?.(country.code)}
                />

                {/* Stress indicator dot (top-right) */}
                <circle cx={pos.x + pos.width - 8} cy={pos.y + 8} r="5" fill={country.color} />

                {/* Country code (compact label) */}
                <text
                  x={pos.x + pos.width / 2}
                  y={pos.y + 20}
                  textAnchor="middle"
                  fontSize="12"
                  fontWeight="bold"
                  fill={country.color}
                  className="pointer-events-none"
                >
                  {country.code}
                </text>

                {/* Country name */}
                <text
                  x={pos.x + pos.width / 2}
                  y={pos.y + 38}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight="600"
                  fill="#0F172A"
                  className="pointer-events-none"
                >
                  {country.name}
                </text>

                {/* Stress level (centered) */}
                <text
                  x={pos.x + pos.width / 2}
                  y={pos.y + pos.height / 2 - 10}
                  textAnchor="middle"
                  fontSize="14"
                  fontWeight="bold"
                  fill={country.color}
                  className="pointer-events-none"
                >
                  {stressText}
                </text>

                {/* Sector label */}
                <text
                  x={pos.x + pos.width / 2}
                  y={pos.y + pos.height / 2 + 8}
                  textAnchor="middle"
                  fontSize="9"
                  fill="#475569"
                  className="pointer-events-none"
                >
                  {country.sector}
                </text>

                {/* Loss amount */}
                {country.loss > 0 && (
                  <text
                    x={pos.x + pos.width / 2}
                    y={pos.y + pos.height - 12}
                    textAnchor="middle"
                    fontSize="10"
                    fontWeight="600"
                    fill={country.color}
                    className="pointer-events-none"
                  >
                    {formatUsd(country.loss)}
                  </text>
                )}
              </g>
            );
          })}

          {/* Shock origin indicator (if scenario label provided) */}
          {scenarioLabel && (
            <g>
              <circle cx="225" cy="160" r="40" fill="none" stroke="#0C6B58" strokeWidth="1.5" opacity="0.4" />
              <circle cx="225" cy="160" r="30" fill="none" stroke="#0C6B58" strokeWidth="1" opacity="0.3" />
              <circle cx="225" cy="160" r="3" fill="#0C6B58" />
            </g>
          )}
        </svg>
      </div>

      {/* Legend */}
      <div className="bg-slate-50 rounded-lg border border-slate-200 p-4">
        <h3 className="text-sm font-semibold text-slate-900 mb-3">
          {locale === "ar" ? "مستوى الإجهاد" : "Stress Level"}
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
          {[
            { label: "Nominal", ar: "طبيعي", color: "#3A7D6C", range: "< 0.20" },
            { label: "Low", ar: "منخفض", color: "#2D6A4F", range: "0.20–0.35" },
            { label: "Guarded", ar: "مراقب", color: "#5E6759", range: "0.35–0.50" },
            { label: "Elevated", ar: "مرتفع", color: "#8B6914", range: "0.50–0.65" },
            { label: "High", ar: "عالي", color: "#A0522D", range: "0.65–0.80" },
            { label: "Severe", ar: "حرج", color: "#8C2318", range: "≥ 0.80" },
          ].map((level, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: level.color }}
              />
              <span className="text-xs text-slate-700">
                {locale === "ar" ? level.ar : level.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Info footer — no false click promise when the caller doesn't wire onCountryClick */}
      <p className="text-xs text-slate-600 mt-4 text-center">
        {locale === "ar"
          ? "استعراض التعرض حسب الدولة • الألوان تمثل مستويات الإجهاد النسبية"
          : "Regional exposure by country • Colors represent relative stress levels"}
      </p>
    </div>
  );
}

export type { GCCImpactMapProps };
