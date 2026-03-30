'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import {
  Play, ArrowRight, MessageSquare, Radio, TrendingUp, AlertTriangle,
  Shield, Network, Layers, GitBranch, Users, BarChart3, Cpu, Terminal, Activity,
} from 'lucide-react'
import Navbar from '@/components/ui/Navbar'
import Footer from '@/components/ui/Footer'
import SectionHeading from '@/components/ui/SectionHeading'
import { getLanguage, type Language } from '@/lib/i18n'

const HP: Record<string, { en: string; ar: string }> = {
  badge: { en: 'Simulation Intelligence Engine', ar: 'محرك ذكاء المحاكاة' },
  heroLine1: { en: 'Simulate What', ar: 'حاكِ ما' },
  heroLine2: { en: 'Happens Next', ar: 'سيحدث لاحقاً' },
  heroDesc: { en: 'Turn real-world inputs into entity graphs, agent behavior, and predictive simulation across GCC scenarios. See the future before it unfolds.', ar: 'حوّل المدخلات الواقعية إلى رسوم بيانية للكيانات وسلوك العملاء ومحاكاة تنبؤية عبر سيناريوهات دول الخليج. شاهد المستقبل قبل أن يتكشف.' },
  enterSystem: { en: 'Enter the System', ar: 'ادخل النظام' },
  viewArch: { en: 'View Architecture', ar: 'عرض البنية' },
  systemOnline: { en: 'System Online', ar: 'النظام متصل' },
  agents: { en: '68 Graph Nodes', ar: '68 عقدة بيانية' },
  gccReady: { en: '5-Layer Model', ar: 'نموذج 5 طبقات' },
  demoTag: { en: 'Demo', ar: 'عرض' },
  demoTitle: { en: 'Watch Deevo Sim in Action', ar: 'شاهد ديفو سيم في العمل' },
  pipeTag: { en: 'Pipeline', ar: 'خط المعالجة' },
  pipeTitle: { en: 'Simulate in 5 Steps', ar: 'محاكاة في 5 خطوات' },
  pipeSub: { en: 'From raw scenario input to explainable prediction — built as a layered intelligence pipeline.', ar: 'من مدخلات السيناريو إلى التنبؤ القابل للتفسير — مبني كخط معالجة استخباراتي متعدد الطبقات.' },
  useCaseTag: { en: 'Use Cases', ar: 'حالات الاستخدام' },
  useCaseTitle: { en: 'Built for GCC Scenarios', ar: 'مصمم لسيناريوهات الخليج' },
  aboutTag: { en: 'About', ar: 'حول' },
  aboutTitle: { en: 'Built to Rehearse Reality', ar: 'مصمم لاستباق الواقع' },
  aboutDesc: { en: 'Deevo Sim creates a digital simulation layer from real-world scenarios, helping teams understand how reactions may spread, evolve, and intensify across connected audiences. Built with GCC context at its core, the platform combines entity extraction, relationship mapping, causal propagation, and predictive analytics into a single intelligence pipeline.', ar: 'يُنشئ ديفو سيم طبقة محاكاة رقمية من سيناريوهات العالم الحقيقي، مما يساعد الفرق على فهم كيف يمكن أن تنتشر ردود الفعل وتتطور وتشتد عبر الجماهير المترابطة. مبني بسياق خليجي في جوهره، يجمع المنصة بين استخراج الكيانات ورسم العلاقات والانتشار السببي والتحليلات التنبؤية في خط معالجة استخباراتي واحد.' },
  enterSim: { en: 'Enter the Simulation', ar: 'ادخل المحاكاة' },
  enterSimDesc: { en: 'Experience the full pipeline — from scenario input to predictive intelligence.', ar: 'اختبر خط المعالجة الكامل — من مدخلات السيناريو إلى الذكاء التنبؤي.' },
  launchSystem: { en: 'Launch System', ar: 'تشغيل النظام' },
  exploreArch: { en: 'Explore Architecture', ar: 'استكشف البنية' },
  seePipeline: { en: 'See the full simulation pipeline', ar: 'شاهد خط المحاكاة الكامل' },
}

function t(key: string, lang: Language): string {
  return HP[key]?.[lang] || key
}

export default function HomePage() {
  const [lang, setLang] = useState<Language>('ar')
  useEffect(() => { setLang(getLanguage()) }, [])

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.2 } },
  }
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] } },
  }

  const steps = [
    { icon: Layers, step: '01', title: { en: 'Input Scenario', ar: 'إدخال السيناريو' }, desc: { en: 'Provide a real-world scenario in Arabic or English — policy changes, market events, social triggers.', ar: 'أدخل سيناريو واقعي بالعربية أو الإنجليزية — تغييرات سياسية، أحداث سوقية، محفزات اجتماعية.' } },
    { icon: Cpu, step: '02', title: { en: 'Extract Entities', ar: 'استخراج الكيانات' }, desc: { en: 'Identify organizations, topics, regions, and platforms from the input.', ar: 'تحديد المنظمات والمواضيع والمناطق والمنصات من المدخلات.' } },
    { icon: GitBranch, step: '03', title: { en: 'Build Graph', ar: 'بناء الرسم البياني' }, desc: { en: 'Map causal relationships — influence, amplification, disruption — into a weighted directed graph.', ar: 'رسم العلاقات السببية — التأثير، التضخيم، التعطيل — في رسم بياني موجه مرجح.' } },
    { icon: Users, step: '04', title: { en: 'Propagate Impact', ar: 'نشر التأثير' }, desc: { en: 'Run BFS propagation: impact(node) = Σ(weight × source_impact) × sensitivity across 5 layers.', ar: 'تشغيل الانتشار: تأثير(عقدة) = مجموع(الوزن × تأثير_المصدر) × الحساسية عبر 5 طبقات.' } },
    { icon: BarChart3, step: '05', title: { en: 'Generate Intelligence', ar: 'إنشاء التقرير الاستخباراتي' }, desc: { en: 'Produce impact analysis, sector breakdowns, causal chains, and confidence-scored predictions.', ar: 'إنتاج تحليل التأثير وتفصيلات القطاعات وسلاسل السببية وتنبؤات مسجلة الثقة.' } },
  ]

  const useCases = [
    { icon: MessageSquare, title: { en: 'Public Reaction', ar: 'ردود الفعل العامة' }, desc: { en: 'Model citizen response to policy changes and government announcements across Gulf demographics.', ar: 'نمذجة استجابة المواطنين لتغييرات السياسات والإعلانات الحكومية عبر التركيبة السكانية الخليجية.' } },
    { icon: Radio, title: { en: 'Media Spread', ar: 'انتشار الإعلام' }, desc: { en: 'Track how news amplifies through media networks, influencer chains, and social platforms.', ar: 'تتبع كيف تنتشر الأخبار عبر شبكات الإعلام وسلاسل المؤثرين والمنصات الاجتماعية.' } },
    { icon: TrendingUp, title: { en: 'Economic Response', ar: 'الاستجابة الاقتصادية' }, desc: { en: 'Simulate market and sentiment shifts following economic events and pricing reforms.', ar: 'محاكاة تحولات السوق والمشاعر بعد الأحداث الاقتصادية وإصلاحات الأسعار.' } },
    { icon: AlertTriangle, title: { en: 'Crisis Cascade', ar: 'تسلسل الأزمات' }, desc: { en: 'Predict how disruptions propagate through infrastructure, finance, and society layers.', ar: 'التنبؤ بكيفية انتشار الاضطرابات عبر طبقات البنية التحتية والمالية والمجتمع.' } },
    { icon: Shield, title: { en: 'Policy Perception', ar: 'تصور السياسات' }, desc: { en: 'Understand how government policies are received across different demographic segments.', ar: 'فهم كيف يتم استقبال السياسات الحكومية عبر شرائح سكانية مختلفة.' } },
    { icon: Network, title: { en: 'Signal Mapping', ar: 'رسم الإشارات' }, desc: { en: 'Map causal pathways and impact propagation across the GCC dependency graph.', ar: 'رسم المسارات السببية وانتشار التأثير عبر رسم التبعية الخليجي.' } },
  ]

  const stats = [
    { value: '68', label: { en: 'Graph Nodes', ar: 'عقدة بيانية' } },
    { value: '149', label: { en: 'Causal Edges', ar: 'رابط سببي' } },
    { value: '5', label: { en: 'System Layers', ar: 'طبقات النظام' } },
  ]

  const demos = [
    { num: '01', title: { en: 'Hormuz Strait Closure', ar: 'إغلاق مضيق هرمز' }, desc: { en: 'Simulating oil transit disruption cascading through infrastructure, economy, and finance layers.', ar: 'محاكاة تعطل عبور النفط المتسلسل عبر طبقات البنية التحتية والاقتصاد والمالية.' } },
    { num: '02', title: { en: 'GCC Aviation Crisis', ar: 'أزمة الطيران الخليجي' }, desc: { en: 'Tracking how fuel price spikes compound with reduced travel demand across airports and society.', ar: 'تتبع كيف تتضاعف ارتفاعات أسعار الوقود مع انخفاض الطلب على السفر عبر المطارات والمجتمع.' } },
  ]

  return (
    <div className="min-h-screen bg-ds-bg text-ds-text" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
      <Navbar />

      {/* HERO */}
      <section id="hero" className="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden">
        <div className="absolute inset-0 ds-grid-bg opacity-60" />
        <div className="absolute w-[600px] h-[600px] -top-20 -left-40 rounded-full bg-ds-accent/8 blur-[160px] pointer-events-none" />
        <div className="absolute w-[500px] h-[500px] bottom-0 right-0 rounded-full bg-purple-600/5 blur-[140px] pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,#06060A_75%)]" />

        <motion.div className="relative z-10 ds-container max-w-5xl mx-auto px-6 text-center" variants={containerVariants} initial="hidden" animate="visible">
          <motion.div variants={itemVariants}>
            <div className="ds-badge-accent inline-flex items-center gap-2 mb-8">
              <Terminal className="w-3.5 h-3.5" />
              <span>{t('badge', lang)}</span>
            </div>
          </motion.div>

          <motion.h1 variants={itemVariants} className="text-display-sm lg:text-display font-bold leading-[1.02] tracking-tight mb-8">
            {t('heroLine1', lang)}<br /><span className="text-ds-accent">{t('heroLine2', lang)}</span>
          </motion.h1>

          <motion.p variants={itemVariants} className="text-body-lg text-ds-text-secondary max-w-2xl mx-auto mb-12 leading-relaxed">
            {t('heroDesc', lang)}
          </motion.p>

          <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/demo" className="ds-btn-primary text-[15px] px-8 py-4">
              {t('enterSystem', lang)} <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/architecture" className="ds-btn-secondary text-[15px] px-8 py-4">
              {t('viewArch', lang)}
            </Link>
          </motion.div>

          <motion.div variants={itemVariants} className="mt-20 flex items-center justify-center gap-4 text-ds-text-dim">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-ds-success animate-pulse" />
              <span className="text-nano font-mono uppercase tracking-wider">{t('systemOnline', lang)}</span>
            </div>
            <span className="text-nano">\u00b7</span>
            <span className="text-nano font-mono uppercase tracking-wider">{t('agents', lang)}</span>
            <span className="text-nano">\u00b7</span>
            <span className="text-nano font-mono uppercase tracking-wider">{t('gccReady', lang)}</span>
          </motion.div>
        </motion.div>
      </section>

      {/* DEMO SECTION */}
      <section className="ds-section">
        <div className="ds-container">
          <SectionHeading tag={t('demoTag', lang)} title={t('demoTitle', lang)} />
          <motion.div className="grid grid-cols-1 lg:grid-cols-5 gap-6" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-60px' }} transition={{ duration: 0.7 }}>
            <div className="lg:col-span-2 flex flex-col gap-5">
              {demos.map((item) => (
                <div key={item.num} className="ds-card-interactive p-7 group">
                  <div className="text-nano font-mono text-ds-accent bg-ds-accent-muted px-2.5 py-1 rounded-md inline-block">{item.num}</div>
                  <h3 className="text-h4 mt-5 group-hover:text-ds-text transition-colors">{item.title[lang]}</h3>
                  <p className="text-caption text-ds-text-secondary mt-3 leading-relaxed">{item.desc[lang]}</p>
                </div>
              ))}
            </div>
            <div className="lg:col-span-3">
              <div className="ds-gradient-border p-[1px] h-full">
                <div className="bg-ds-surface rounded-ds-xl h-full min-h-[360px] flex flex-col items-center justify-center relative overflow-hidden">
                  <div className="absolute inset-0 ds-grid-bg opacity-30" />
                  <div className="relative z-10 flex flex-col items-center">
                    <Link href="/demo" className="w-18 h-18 rounded-full bg-ds-accent/10 border border-ds-accent/25 flex items-center justify-center cursor-pointer hover:bg-ds-accent/18 hover:border-ds-accent/40 transition-all duration-300 hover:shadow-ds-glow-accent">
                      <Play className="w-7 h-7 text-ds-accent ml-0.5" />
                    </Link>
                    <p className="text-caption text-ds-text-secondary mt-5">{t('seePipeline', lang)}</p>
                  </div>
                  <div className="absolute bottom-5 right-5 flex items-center gap-2 text-nano font-mono bg-ds-bg/80 backdrop-blur-sm px-3 py-1.5 rounded-ds border border-ds-border/50">
                    <Activity className="w-3 h-3 text-ds-accent" />
                    LIVE
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* 5-STEP PIPELINE */}
      <section className="ds-section bg-ds-bg-alt">
        <div className="ds-container">
          <SectionHeading tag={t('pipeTag', lang)} title={t('pipeTitle', lang)} subtitle={t('pipeSub', lang)} />
          <motion.div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-60px' }} transition={{ duration: 0.7 }}>
            {steps.map((item, idx) => {
              const IconComponent = item.icon
              return (
                <motion.div key={idx} className="ds-card p-7 flex flex-col group hover:border-ds-accent/15 transition-all duration-300" initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: idx * 0.08, duration: 0.6 }}>
                  <div className="w-10 h-10 rounded-ds bg-ds-surface-raised border border-ds-border flex items-center justify-center mb-5 group-hover:border-ds-accent/20 transition-colors">
                    <IconComponent className="w-[18px] h-[18px] text-ds-text-muted group-hover:text-ds-accent transition-colors" />
                  </div>
                  <div className="text-nano font-mono text-ds-accent-dim">{item.step}</div>
                  <h3 className="text-h4 mt-2">{item.title[lang]}</h3>
                  <p className="text-caption text-ds-text-secondary mt-2.5 flex-grow leading-relaxed">{item.desc[lang]}</p>
                </motion.div>
              )
            })}
          </motion.div>
        </div>
      </section>

      {/* USE CASES */}
      <section className="ds-section">
        <div className="ds-container">
          <SectionHeading tag={t('useCaseTag', lang)} title={t('useCaseTitle', lang)} />
          <motion.div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-60px' }} transition={{ duration: 0.7 }}>
            {useCases.map((item, idx) => {
              const IconComponent = item.icon
              return (
                <motion.div key={idx} className="ds-card-interactive p-7" initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: idx * 0.06, duration: 0.6 }}>
                  <div className="w-11 h-11 rounded-ds bg-ds-accent-muted flex items-center justify-center">
                    <IconComponent className="w-5 h-5 text-ds-accent" />
                  </div>
                  <h3 className="text-h4 mt-5">{item.title[lang]}</h3>
                  <p className="text-caption text-ds-text-secondary mt-2.5 leading-relaxed">{item.desc[lang]}</p>
                </motion.div>
              )
            })}
          </motion.div>
        </div>
      </section>

      {/* ABOUT */}
      <section id="about" className="ds-section bg-ds-bg-alt">
        <div className="ds-container">
          <SectionHeading tag={t('aboutTag', lang)} title={t('aboutTitle', lang)} />
          <motion.div className="max-w-3xl mx-auto" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-60px' }} transition={{ duration: 0.7 }}>
            <p className="text-body-lg text-ds-text-secondary leading-relaxed text-center">{t('aboutDesc', lang)}</p>
            <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-6">
              {stats.map((stat, idx) => (
                <motion.div key={idx} className="ds-card p-6 text-center" initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: idx * 0.1, duration: 0.5 }}>
                  <div className="text-h1 text-ds-accent font-mono font-bold">{stat.value}</div>
                  <div className="text-micro text-ds-text-muted mt-2 uppercase tracking-wider">{stat.label[lang]}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="ds-section">
        <div className="ds-container">
          <motion.div className="ds-gradient-border p-[1px] max-w-3xl mx-auto" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-60px' }} transition={{ duration: 0.7 }}>
            <div className="ds-card p-14 lg:p-20 rounded-ds-xl text-center bg-gradient-to-br from-ds-surface to-ds-bg">
              <h2 className="text-h2 lg:text-h1 text-ds-text">{t('enterSim', lang)}</h2>
              <p className="text-body-lg text-ds-text-secondary mt-4 max-w-xl mx-auto">{t('enterSimDesc', lang)}</p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center mt-10">
                <Link href="/demo" className="ds-btn-primary text-[15px] px-8 py-4">{t('launchSystem', lang)} <ArrowRight className="w-4 h-4" /></Link>
                <Link href="/architecture" className="ds-btn-secondary text-[15px] px-8 py-4">{t('exploreArch', lang)}</Link>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
