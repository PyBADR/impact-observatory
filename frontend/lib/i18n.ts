/* =================================================
    Deevo Sim v2 — Internationalization System
    Bilingual Arabic + English Support
   ================================================= */

import type { BilingualText } from './types'

export type Language = 'en' | 'ar'

// — Language State —————————————————————————————

let currentLanguage: Language = 'en'

export function setLanguage(lang: Language) {
  currentLanguage = lang
  if (typeof document !== 'undefined') {
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
    document.documentElement.lang = lang
  }
}

export function getLanguage(): Language {
  return currentLanguage
}

// — Text Resolution ———————————————————————————

export function t(text: BilingualText | undefined, fallback = ''): string {
  if (!text) return fallback
  return currentLanguage === 'ar' ? text.ar : text.en
}

export function tField(en: string | undefined, ar: string | undefined): string {
  if (currentLanguage === 'ar' && ar) return ar
  return en || ''
}

// — Direction Utilities ————————————————————————

export function isRTL(): boolean {
  return currentLanguage === 'ar'
}

export function dirClass(): string {
  return currentLanguage === 'ar' ? 'rtl' : 'ltr'
}

export function textAlignClass(): string {
  return currentLanguage === 'ar' ? 'text-right' : 'text-left'
}

// — Static Labels ————————————————————————————

export const labels: Record<string, BilingualText> = {
  controlRoom: { en: 'Control Room', ar: 'غرفة التحكم' },
  scenarioInput: { en: 'Scenario Input', ar: 'إدخال السيناريو' },
  runSimulation: { en: 'Run Simulation', ar: 'تشغيل المحاكاة' },
  decisionOutput: { en: 'Decision Output', ar: 'مخرجات القرار' },
  intelligenceBrief: { en: 'Intelligence Brief', ar: 'موجز استخباراتي' },
  scenarioLibrary: { en: 'Scenario Library', ar: 'مكتبة السيناريوهات' },
  analyst: { en: 'Analyst', ar: 'محلل' },
  risk: { en: 'Risk', ar: 'مخاطر' },
  spread: { en: 'Spread', ar: 'الانتشار' },
  sentiment: { en: 'Sentiment', ar: 'المشاعر' },
  presets: { en: 'Presets', ar: 'الإعدادات المسبقة' },
  ready: { en: 'READY', ar: 'جاهز' },
  simulating: { en: 'SIMULATING', ar: 'المحاكاة جارية' },
  complete: { en: 'COMPLETE', ar: 'مكتمل' },
  region: { en: 'Region', ar: 'المنطقة' },
  domain: { en: 'Domain', ar: 'المجال' },
  trigger: { en: 'Trigger', ar: 'المحفز' },
  actors: { en: 'Actors', ar: 'الأطراف' },
  signals: { en: 'Signals', ar: 'الإشارات' },
  businessImpact: { en: 'Business Impact', ar: 'التأثير التجاري' },
  financialImpact: { en: 'Financial Impact', ar: 'التأثير المالي' },
  customerImpact: { en: 'Customer Impact', ar: 'تأثير العملاء' },
  regulatoryRisk: { en: 'Regulatory Risk', ar: 'المخاطر التنظيمية' },
  reputationDamage: { en: 'Reputation', ar: 'السمعة' },
}

// — Domain Labels ———————————————————————————

export const domainLabels: Record<string, BilingualText> = {
  energy: { en: 'Energy', ar: 'الطاقة' },
  telecom: { en: 'Telecom', ar: 'الاتصالات' },
  banking: { en: 'Banking', ar: 'البنوك' },
  insurance: { en: 'Insurance', ar: 'التأمين' },
  policy: { en: 'Policy', ar: 'السياسات' },
  brand: { en: 'Brand / Media', ar: 'العلامة التجارية' },
  'supply-chain': { en: 'Supply Chain', ar: 'سلسلة التوريد' },
  security: { en: 'Cyber Security', ar: 'الأمن السيبراني' },
}

export const regionLabels: Record<string, BilingualText> = {
  gcc: { en: 'GCC', ar: 'دول الخليج' },
  saudi: { en: 'Saudi Arabia', ar: 'السعودية' },
  kuwait: { en: 'Kuwait', ar: 'الكويت' },
  uae: { en: 'UAE', ar: 'الإمارات' },
  qatar: { en: 'Qatar', ar: 'قطر' },
  bahrain: { en: 'Bahrain', ar: 'البحرين' },
  oman: { en: 'Oman', ar: 'عمان' },
}

export const triggerLabels: Record<string, BilingualText> = {
  'price-change': { en: 'Price Change', ar: 'تغيير الأسعار' },
  leak: { en: 'Leak', ar: 'تسريب' },
  announcement: { en: 'Announcement', ar: 'إعلان' },
  rumor: { en: 'Rumor', ar: 'إشاعة' },
  incident: { en: 'Incident', ar: 'حادثة' },
  regulatory: { en: 'Regulatory Action', ar: 'إجراء تنظيمي' },
  cyberattack: { en: 'Cyber Attack', ar: 'هجوم سيبراني' },
  fraud: { en: 'Fraud Detection', ar: 'كشف احتيال' },
}

// — Helper Functions (resolve labels by key) —————————

export function label(key: string): string {
  const entry = labels[key]
  if (!entry) return key
  return currentLanguage === 'ar' ? entry.ar : entry.en
}

export function domainLabel(key: string): string {
  const entry = domainLabels[key]
  if (!entry) return key
  return currentLanguage === 'ar' ? entry.ar : entry.en
}

export function regionLabel(key: string): string {
  const entry = regionLabels[key]
  if (!entry) return key
  return currentLanguage === 'ar' ? entry.ar : entry.en
}

export function triggerLabel(key: string): string {
  const entry = triggerLabels[key]
  if (!entry) return key
  return currentLanguage === 'ar' ? entry.ar : entry.en
                  }
