import type { MacroInput } from "@/types/decision";

export const SCENARIOS: Record<string, { label: string; labelAr: string; macro: MacroInput }> = {
  recession: {
    label: "Recession",
    labelAr: "ركود اقتصادي",
    macro: { inflation: 7, interestRate: 8, gdpGrowth: -2 },
  },
  oilShock: {
    label: "Oil Shock",
    labelAr: "صدمة نفطية",
    macro: { inflation: 9, interestRate: 7, gdpGrowth: 1 },
  },
  boom: {
    label: "Economic Boom",
    labelAr: "ازدهار اقتصادي",
    macro: { inflation: 3, interestRate: 4, gdpGrowth: 5 },
  },
  stagflation: {
    label: "Stagflation",
    labelAr: "ركود تضخمي",
    macro: { inflation: 8, interestRate: 6, gdpGrowth: -1 },
  },
  creditCrunch: {
    label: "Credit Crunch",
    labelAr: "أزمة ائتمان",
    macro: { inflation: 5, interestRate: 10, gdpGrowth: 0 },
  },
};
