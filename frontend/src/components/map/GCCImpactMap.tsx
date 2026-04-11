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
  if (stress < 0.2) return "#10b981"; // emerald
  if (stress < 0.4) return "#fbbf24"; // yellow
  if (stress < 0.6) return "#f97316"; // amber
  if (stress < 0.8) return "#f97316"; // orange
  return "#ef4444"; // red
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
    <div className="w-full bg-gradient-to-b from-gray-900 to-gray-950 rounded-lg p-6 text-white">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">{title}</h2>
        {scenarioLabel && (
          <p className="text-sm text-gray-400">
            {locale === "ar" ? "السيناريو: " : "Scenario: "}
            <span className="text-amber-300 font-semibold">{scenarioLabel}</span>
          </p>
        )}
      </div>

      {/* SVG Map Container */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6 overflow-x-auto" dir={textDir}>
        <svg viewBox="0 0 450 320" className="w-full min-w-[600px] h-auto" xmlns="http://www.w3.org/2000/svg">
          {/* Water/background */}
          <rect width="450" height="320" fill="#1a202c" />

          {/* Grid reference lines (subtle) */}
          <g stroke="#374151" strokeWidth="0.5" opacity="0.3">
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
                  opacity="0.15"
                  stroke={country.color}
                  strokeWidth="2"
                  className="cursor-pointer hover:opacity-25 transition-opacity"
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
                  fill="white"
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
                  fill="#e5e7eb"
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
              <circle cx="225" cy="160" r="40" fill="none" stroke="#fbbf24" strokeWidth="1.5" opacity="0.4" />
              <circle cx="225" cy="160" r="30" fill="none" stroke="#fbbf24" strokeWidth="1" opacity="0.3" />
              <circle cx="225" cy="160" r="3" fill="#fbbf24" />
            </g>
          )}
        </svg>
      </div>

      {/* Legend */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">
          {locale === "ar" ? "مستوى الإجهاد" : "Stress Level"}
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
          {[
            { label: "Nominal", ar: "طبيعي", color: "#10b981", range: "< 0.2" },
            { label: "Low", ar: "منخفض", color: "#fbbf24", range: "0.2–0.4" },
            { label: "Guarded", ar: "مراقب", color: "#f97316", range: "0.4–0.6" },
            { label: "Elevated", ar: "مرتفع", color: "#f97316", range: "0.6–0.8" },
            { label: "High", ar: "عالي", color: "#ef4444", range: "0.8–1.0" },
            { label: "Severe", ar: "حرج", color: "#7f1d1d", range: "> 0.8" },
          ].map((level, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: level.color }}
              />
              <span className="text-xs text-gray-400">
                {locale === "ar" ? level.ar : level.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Info footer */}
      <p className="text-xs text-gray-500 mt-4 text-center">
        {locale === "ar"
          ? "انقر على البلد لعرض التفاصيل • الألوان تمثل مستويات الإجهاد النسبية"
          : "Click a country for details • Colors represent relative stress levels"}
      </p>
    </div>
  );
}

export type { GCCImpactMapProps };
