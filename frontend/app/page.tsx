'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getLanguage, setLanguage, type Language } from '@/lib/i18n'
import Navbar from '@/components/ui/Navbar'
import Footer from '@/components/ui/Footer'

/* ════════════════════════════════════════════════════
   Impact Observatory | مرصد الأثر — Landing Page
   Boardroom executive entry. White, clean, financial-first.
   ════════════════════════════════════════════════════ */

const L = {
  title_en: 'Impact Observatory',
  title_ar: 'مرصد الأثر',
  headline_en: 'Understand financial impact before it happens',
  headline_ar: 'افهم الأثر المالي قبل حدوثه',
  sub_en: 'GCC Decision Intelligence Platform — Transform complex events into financial loss quantification, sector stress analysis, and actionable decisions.',
  sub_ar: 'منصة ذكاء القرار في دول الخليج — حوّل الأحداث المعقدة إلى قياس الخسائر المالية وتحليل ضغط القطاعات وقرارات قابلة للتنفيذ.',
  cta_en: 'Run Scenario',
  cta_ar: 'تشغيل سيناريو',
  cta2_en: 'View Dashboard',
  cta2_ar: 'عرض لوحة القيادة',

  // What it does
  what_title_en: 'What It Does',
  what_title_ar: 'ماذا يفعل',
  what_desc_en: 'Impact Observatory maps the chain reaction from any major event — geopolitical disruption, natural disaster, or economic shock — through a 10-stage analytical pipeline, producing quantified financial impact across every GCC financial sector.',
  what_desc_ar: 'مرصد الأثر يرسم سلسلة التأثير من أي حدث كبير — اضطراب جيوسياسي أو كارثة طبيعية أو صدمة اقتصادية — عبر خط تحليلي من 10 مراحل، لإنتاج أثر مالي كمّي عبر كل القطاعات المالية الخليجية.',

  // Sections
  fin_title_en: 'Financial Impact',
  fin_title_ar: 'الأثر المالي',
  fin_desc_en: 'Headline loss quantification in billions USD. Peak stress day. Time-to-failure countdown. Severity classification from LOW to CRITICAL.',
  fin_desc_ar: 'قياس الخسارة الرئيسية بمليارات الدولارات. يوم الذروة. العد التنازلي للانهيار. تصنيف الشدة من منخفض إلى حرج.',

  bank_title_en: 'Banking Stress',
  bank_title_ar: 'ضغط القطاع البنكي',
  bank_desc_en: 'Capital adequacy ratio vs Basel III floor. Liquidity gap. Interbank rate spike. FX reserve drawdown. Time-to-liquidity-breach.',
  bank_desc_ar: 'نسبة كفاية رأس المال مقابل حد بازل 3. فجوة السيولة. ارتفاع سعر الإنتربنك. سحب الاحتياطيات الأجنبية.',

  ins_title_en: 'Insurance Stress',
  ins_title_ar: 'ضغط التأمين',
  ins_desc_en: 'Claims surge percentage. Reinsurance treaty trigger. Combined ratio. Solvency margin. Time-to-insolvency.',
  ins_desc_ar: 'نسبة ارتفاع المطالبات. تفعيل إعادة التأمين. النسبة المجمعة. هامش الملاءة. الوقت للإعسار.',

  fin_tech_title_en: 'Fintech Disruption',
  fin_tech_title_ar: 'اضطراب الفنتك',
  fin_tech_desc_en: 'Payment failure rate. Settlement delay hours. Gateway downtime. Digital banking disruption score. Time-to-payment-failure.',
  fin_tech_desc_ar: 'معدل فشل المدفوعات. تأخير التسوية. توقف البوابة. اضطراب البنوك الرقمية. الوقت لفشل المدفوعات.',

  dec_title_en: 'Decision Intelligence',
  dec_title_ar: 'ذكاء القرار',
  dec_desc_en: 'Multi-objective optimization producing top 3 actions. Cost vs loss avoided. Priority scoring. Regulatory risk assessment. Execution timeline.',
  dec_desc_ar: 'تحسين متعدد الأهداف ينتج أفضل 3 إجراءات. التكلفة مقابل الخسارة المتجنبة. تسجيل الأولوية. تقييم المخاطر التنظيمية.',

  // Pipeline section
  pipe_title_en: '10-Stage Analytical Pipeline',
  pipe_title_ar: 'خط تحليلي من 10 مراحل',

  // V1
  v1_badge_en: 'V1 PROGRAM',
  v1_badge_ar: 'البرنامج الأول',
  v1_title_en: 'Hormuz Strait Closure',
  v1_title_ar: 'إغلاق مضيق هرمز',
  v1_desc_en: '14-day blockage, severity 0.85. $624.75B headline loss. CRITICAL across banking and fintech. 3 coordinated response actions.',
  v1_desc_ar: 'إغلاق 14 يوم، شدة 0.85. خسارة 624.75 مليار دولار. حرج عبر البنوك والفنتك. 3 إجراءات استجابة منسقة.',
}

const PIPELINE_STAGES = [
  { id: 'scenario',       en: 'Event Scenario',    ar: 'سيناريو الحدث' },
  { id: 'physics',        en: 'System Stress',     ar: 'ضغط النظام' },
  { id: 'graph_snapshot', en: 'Graph Snapshot',     ar: 'لقطة الرسم' },
  { id: 'propagation',    en: 'Impact Chain',       ar: 'سلسلة الأثر' },
  { id: 'financial',      en: 'Financial Impact',   ar: 'الأثر المالي' },
  { id: 'sector_risk',    en: 'Sector Risk',        ar: 'مخاطر القطاع' },
  { id: 'regulatory',     en: 'Regulatory Check',   ar: 'الفحص التنظيمي' },
  { id: 'decision',       en: 'Decision Actions',   ar: 'إجراءات القرار' },
  { id: 'explanation',    en: 'Explanation',         ar: 'التفسير' },
  { id: 'output',         en: 'Output',             ar: 'المخرجات' },
]

const CAPABILITY_CARDS = [
  { key: 'fin',      icon: '📊' },
  { key: 'bank',     icon: '🏦' },
  { key: 'ins',      icon: '🛡' },
  { key: 'fin_tech', icon: '💳' },
  { key: 'dec',      icon: '🎯' },
]

export default function LandingPage() {
  const [lang, setLang] = useState<Language>('ar')
  useEffect(() => { setLang(getLanguage()) }, [])
  const isAR = lang === 'ar'
  const t = (key: string) => (L as any)[`${key}_${lang}`] ?? (L as any)[`${key}_en`] ?? key

  return (
    <div dir={isAR ? 'rtl' : 'ltr'} className="min-h-screen bg-ds-bg">
      <Navbar />

      {/* ══════ HERO ══════ */}
      <section className="ds-container pt-32 pb-20 lg:pt-40 lg:pb-28">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-ds-lg bg-ds-accent/10 border border-ds-accent/20 flex items-center justify-center">
              <span className="text-ds-accent font-bold text-base">IO</span>
            </div>
            <span className="text-body-lg font-semibold text-ds-text tracking-tight">
              {t('title')}
            </span>
          </div>

          <h1 className="text-display text-ds-text mb-6 leading-tight">
            {t('headline')}
          </h1>

          <p className="text-body-lg text-ds-text-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
            {t('sub')}
          </p>

          <div className="flex items-center justify-center gap-4">
            <Link href="/dashboard" className="ds-btn-primary text-body">
              {t('cta')}
            </Link>
            <Link href="/dashboard" className="ds-btn-secondary text-body">
              {t('cta2')}
            </Link>
          </div>
        </div>
      </section>

      {/* ══════ V1 PROGRAM BANNER ══════ */}
      <section className="ds-container pb-16">
        <div className="max-w-4xl mx-auto bg-ds-card border border-ds-accent/15 rounded-ds-xl p-8 shadow-ds-md">
          <div className="flex items-start gap-6">
            <div className="flex-shrink-0">
              <span className="ds-badge-accent text-micro font-bold tracking-widest">
                {t('v1_badge')}
              </span>
            </div>
            <div>
              <h3 className="text-h3 text-ds-text mb-2">{t('v1_title')}</h3>
              <p className="text-body text-ds-text-secondary">{t('v1_desc')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ══════ WHAT IT DOES ══════ */}
      <section className="ds-section bg-ds-surface border-y border-ds-border">
        <div className="ds-container">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="text-h1 text-ds-text mb-4">{t('what_title')}</h2>
            <p className="text-body-lg text-ds-text-secondary leading-relaxed">
              {t('what_desc')}
            </p>
          </div>

          {/* Capability Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {CAPABILITY_CARDS.map(({ key, icon }) => (
              <div key={key} className="ds-card p-6 hover:shadow-ds-md transition-shadow">
                <div className="text-2xl mb-4">{icon}</div>
                <h3 className="text-h4 text-ds-text mb-2">{t(`${key}_title`)}</h3>
                <p className="text-caption text-ds-text-secondary leading-relaxed">
                  {t(`${key}_desc`)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════ PIPELINE ══════ */}
      <section className="ds-section">
        <div className="ds-container">
          <h2 className="text-h1 text-ds-text text-center mb-12">{t('pipe_title')}</h2>
          <div className="max-w-4xl mx-auto">
            <div className="flex flex-wrap items-center justify-center gap-3">
              {PIPELINE_STAGES.map((stage, i) => (
                <div key={stage.id} className="flex items-center gap-3">
                  <div className="ds-flow-stage">
                    <span className="w-5 h-5 rounded-full bg-ds-accent/10 text-ds-accent text-[10px] font-bold flex items-center justify-center flex-shrink-0">
                      {i + 1}
                    </span>
                    <span>{isAR ? stage.ar : stage.en}</span>
                  </div>
                  {i < PIPELINE_STAGES.length - 1 && (
                    <svg className="w-4 h-4 text-ds-text-dim flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isAR ? "M19 12H5M5 12l4 4M5 12l4-4" : "M5 12h14M19 12l-4-4M19 12l-4 4"} />
                    </svg>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ══════ CTA FOOTER ══════ */}
      <section className="ds-section bg-ds-surface border-t border-ds-border">
        <div className="ds-container text-center">
          <h2 className="text-h2 text-ds-text mb-4">
            {isAR ? 'ابدأ بتحليل أول سيناريو' : 'Start your first scenario analysis'}
          </h2>
          <p className="text-body text-ds-text-secondary mb-8 max-w-lg mx-auto">
            {isAR
              ? 'قم بتشغيل سيناريو إغلاق مضيق هرمز لرؤية الأثر المالي عبر جميع القطاعات.'
              : 'Run the Hormuz Strait Closure scenario to see financial impact across all sectors.'}
          </p>
          <Link href="/dashboard" className="ds-btn-primary text-body">
            {t('cta')}
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  )
}
