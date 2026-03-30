'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import {
  FileText, Search, GitBranch, Zap, BarChart3, ChevronRight,
  Layers, Code2, Terminal, Globe, Activity,
} from 'lucide-react'
import Navbar from '@/components/ui/Navbar'
import Footer from '@/components/ui/Footer'
import SectionHeading from '@/components/ui/SectionHeading'
import { getLanguage, type Language } from '@/lib/i18n'

const AP: Record<string, { en: string; ar: string }> = {
  badge: { en: 'Architecture', ar: 'البنية' },
  title: { en: 'System Architecture', ar: 'بنية النظام' },
  subtitle: { en: 'A 5-layer causal intelligence engine with mathematical propagation model.', ar: 'محرك ذكاء سببي من 5 طبقات مع نموذج انتشار رياضي.' },
  pipelineTitle: { en: 'Pipeline Overview', ar: 'نظرة عامة على خط المعالجة' },
  deepDive: { en: 'Deep Dive', ar: 'تعمّق' },
  archTitle: { en: 'Pipeline Architecture', ar: 'بنية خط المعالجة' },
  archSub: { en: 'Each stage processes, transforms, and enriches the scenario data as it flows through the system.', ar: 'كل مرحلة تعالج وتحول وتثري بيانات السيناريو أثناء تدفقها عبر النظام.' },
  formulaTag: { en: 'Mathematical Model', ar: 'النموذج الرياضي' },
  formulaTitle: { en: 'Propagation Formula', ar: 'معادلة الانتشار' },
  formulaSub: { en: 'The causal engine that drives every simulation — mathematically grounded, fully explainable.', ar: 'المحرك السببي الذي يقود كل محاكاة — مبني رياضياً، قابل للتفسير بالكامل.' },
  layerTag: { en: '5-Layer Model', ar: 'نموذج الطبقات الخمس' },
  layerTitle: { en: 'GCC Dependency Layers', ar: 'طبقات التبعية الخليجية' },
  stackTag: { en: 'Stack', ar: 'التقنيات' },
  stackTitle: { en: 'Technology', ar: 'التقنيات المستخدمة' },
  frontend: { en: 'Frontend', ar: 'الواجهة الأمامية' },
  engine: { en: 'Engine', ar: 'المحرك' },
  seeAction: { en: 'See It in Action', ar: 'شاهدها في العمل' },
  seeActionDesc: { en: 'Experience the full pipeline from scenario input to predictive intelligence.', ar: 'اختبر خط المعالجة الكامل من إدخال السيناريو إلى الذكاء التنبؤي.' },
  launchSystem: { en: 'Launch System', ar: 'تشغيل النظام' },
  backHome: { en: 'Back to Home', ar: 'العودة للرئيسية' },
}

function t(key: string, lang: Language): string {
  return AP[key]?.[lang] || key
}

export default function ArchitecturePage() {
  const [lang, setLang] = useState<Language>('ar')
  useEffect(() => { setLang(getLanguage()) }, [])

  const pipelineNodes = [
    { label: { en: 'Input', ar: 'إدخال' }, icon: FileText },
    { label: { en: 'Parse', ar: 'تحليل' }, icon: Search },
    { label: { en: 'Graph', ar: 'رسم' }, icon: GitBranch },
    { label: { en: 'Propagate', ar: 'انتشار' }, icon: Zap },
    { label: { en: 'Analyze', ar: 'تحليل' }, icon: BarChart3 },
    { label: { en: 'Report', ar: 'تقرير' }, icon: Globe },
  ]

  const archBlocks = [
    { step: '01', icon: FileText, title: { en: 'Scenario Input', ar: 'إدخال السيناريو' }, desc: { en: 'Users select from 8 pre-built GCC risk scenarios or configure custom shock vectors. Each scenario defines initial impact nodes and severity levels.', ar: 'يختار المستخدمون من 8 سيناريوهات مخاطر خليجية مبنية مسبقاً أو يضبطون متجهات صدمة مخصصة. كل سيناريو يحدد عقد التأثير الأولية ومستويات الحدة.' }, features: [{ en: 'Bilingual AR/EN', ar: 'ثنائي اللغة' }, { en: '8 risk scenarios', ar: '8 سيناريوهات مخاطر' }, { en: 'Severity slider', ar: 'شريط الحدة' }, { en: 'Shock vector config', ar: 'ضبط متجه الصدمة' }] },
    { step: '02', icon: Search, title: { en: 'Entity Graph', ar: 'رسم الكيانات' }, desc: { en: '68 real GCC entities across 5 layers — geography, infrastructure, economy, finance, society — connected by 149 weighted causal edges with explicit polarity.', ar: '68 كياناً خليجياً حقيقياً عبر 5 طبقات — الجغرافيا، البنية التحتية، الاقتصاد، المالية، المجتمع — مرتبطة بـ 149 رابط سببي مرجح مع قطبية صريحة.' }, features: [{ en: '68 nodes', ar: '68 عقدة' }, { en: '149 weighted edges', ar: '149 رابط مرجح' }, { en: '5 causal layers', ar: '5 طبقات سببية' }, { en: 'Bilingual labels', ar: 'تسميات ثنائية اللغة' }] },
    { step: '03', icon: Zap, title: { en: 'Propagation Engine', ar: 'محرك الانتشار' }, desc: { en: 'Multi-iteration causal propagation with decay. Formula: I(t+1) = Σ(w×p×I(t)) × sensitivity - decay × I(t). Bounded [-1,1]. System energy: E = Σ impact². Polarity-aware edges.', ar: 'انتشار سببي متعدد المراحل مع اضمحلال. المعادلة: I(t+1) = Σ(w×p×I(t)) × الحساسية - اضمحلال × I(t). محدود [-1,1]. طاقة النظام: E = Σ التأثير². روابط واعية بالقطبية.' }, features: [{ en: 'Mathematical model', ar: 'نموذج رياضي' }, { en: 'BFS propagation', ar: 'انتشار BFS' }, { en: 'Dampening factor', ar: 'معامل تخميد' }, { en: 'Causal chain tracking', ar: 'تتبع السلسلة السببية' }] },
    { step: '04', icon: BarChart3, title: { en: 'Impact Analysis', ar: 'تحليل التأثير' }, desc: { en: 'Sector-level aggregation, top driver identification, economic loss estimation using GDP base values. Confidence scoring based on propagation chain completeness.', ar: 'تجميع على مستوى القطاع، تحديد أهم المحركات، تقدير الخسائر الاقتصادية باستخدام قيم الناتج المحلي الأساسية. تسجيل الثقة بناءً على اكتمال سلسلة الانتشار.' }, features: [{ en: 'Sector breakdown', ar: 'تفصيل قطاعي' }, { en: 'Loss estimation', ar: 'تقدير الخسائر' }, { en: 'Confidence scoring', ar: 'تسجيل الثقة' }, { en: 'Driver ranking', ar: 'ترتيب المحركات' }] },
    { step: '05', icon: Globe, title: { en: 'Dual Visualization', ar: 'التصور المزدوج' }, desc: { en: 'Synchronized graph + globe views. Both use identical runtime data — same nodes, same edges, same impact values, same propagation paths.', ar: 'عروض رسم بياني + كرة أرضية متزامنة. كلاهما يستخدم بيانات تشغيل متطابقة — نفس العقد، نفس الروابط، نفس قيم التأثير، نفس مسارات الانتشار.' }, features: [{ en: 'SVG graph view', ar: 'عرض رسم SVG' }, { en: '3D globe view', ar: 'عرض كرة ثلاثية الأبعاد' }, { en: 'Identical data', ar: 'بيانات متطابقة' }, { en: 'Impact glow', ar: 'توهج التأثير' }] },
    { step: '06', icon: Activity, title: { en: 'Intelligence Brief', ar: 'الموجز الاستخباراتي' }, desc: { en: 'Full bilingual output — causal chains, sector impacts, top drivers, explanation text, spread level, confidence score. All generated from the mathematical model.', ar: 'مخرجات ثنائية اللغة بالكامل — سلاسل سببية، تأثيرات قطاعية، أهم المحركات، نص تفسيري، مستوى الانتشار، درجة الثقة. كلها مولدة من النموذج الرياضي.' }, features: [{ en: 'Bilingual output', ar: 'مخرجات ثنائية' }, { en: 'Causal explanation', ar: 'تفسير سببي' }, { en: 'Spread analysis', ar: 'تحليل الانتشار' }, { en: 'Exportable data', ar: 'بيانات قابلة للتصدير' }] },
  ]

  const layers = [
    { name: { en: 'Geography', ar: 'الجغرافيا' }, color: '#2DD4A0', nodes: { en: 'Saudi Arabia, UAE, Kuwait, Qatar, Oman, Bahrain, Hormuz', ar: 'السعودية، الإمارات، الكويت، قطر، عُمان، البحرين، هرمز' }, count: 7 },
    { name: { en: 'Infrastructure', ar: 'البنية التحتية' }, color: '#F5A623', nodes: { en: 'RUH/DXB/KWI/DOH Airports, Jebel Ali/Dammam/Doha Ports, Power Grid, Desalination', ar: 'مطارات الرياض/دبي/الكويت/الدوحة، موانئ جبل علي/الدمام/الدوحة، شبكة الكهرباء، التحلية' }, count: 9 },
    { name: { en: 'Economy', ar: 'الاقتصاد' }, color: '#5B7BF8', nodes: { en: 'Oil Export, Aramco, ADNOC, KPC, Shipping, Aviation, Fuel, GDP, Tourism', ar: 'صادرات النفط، أرامكو، أدنوك، KPC، الشحن، الطيران، الوقود، الناتج المحلي، السياحة' }, count: 9 },
    { name: { en: 'Finance', ar: 'المالية' }, color: '#A78BFA', nodes: { en: 'SAMA, UAE CB, Kuwait CB, Tadawul, Insurers, Reinsurers, Insurance Risk', ar: 'مؤسسة النقد، مصرف الإمارات، بنك الكويت، تداول، شركات التأمين، إعادة التأمين، مخاطر التأمين' }, count: 7 },
    { name: { en: 'Society', ar: 'المجتمع' }, color: '#EF5454', nodes: { en: 'Citizens, Travelers, Businesses, Media, Social, Travel Demand, Tickets', ar: 'المواطنون، المسافرون، الشركات، الإعلام، المنصات الاجتماعية، الطلب على السفر، التذاكر' }, count: 7 },
  ]

  const frontendTechs = ['Next.js 14', 'TypeScript', 'Tailwind CSS', 'Framer Motion', 'Pure SVG Graph', 'react-globe.gl']
  const engineTechs = [
    { en: 'BFS Propagation', ar: 'انتشار BFS' },
    { en: 'Causal Graph Model', ar: 'نموذج الرسم السببي' },
    { en: 'Dampened Impact Chain', ar: 'سلسلة تأثير مخمدة' },
    { en: 'GDP Loss Estimation', ar: 'تقدير خسائر الناتج المحلي' },
    { en: 'Confidence Scoring', ar: 'تسجيل الثقة' },
  ]

  return (
    <div className="bg-ds-bg min-h-screen flex flex-col" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
      <Navbar />

      {/* HERO */}
      <motion.section className="pt-34 pb-22 bg-ds-bg relative overflow-hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
        <div className="absolute inset-0 ds-grid-bg opacity-30" />
        <div className="ds-container text-center relative z-10">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <span className="ds-badge-accent inline-flex items-center gap-1.5 mb-6"><Layers className="w-3.5 h-3.5" />{t('badge', lang)}</span>
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="text-display-sm lg:text-display text-ds-text font-bold">{t('title', lang)}</motion.h1>
          <motion.p initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="text-body-lg text-ds-text-secondary max-w-3xl mx-auto mt-6">{t('subtitle', lang)}</motion.p>
        </div>
      </motion.section>

      {/* PIPELINE OVERVIEW */}
      <motion.section className="ds-section-tight bg-ds-bg" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container">
          <h2 className="text-h3 text-center mb-12 text-ds-text">{t('pipelineTitle', lang)}</h2>
          <div className="hidden lg:flex items-center justify-center gap-0">
            {pipelineNodes.map((node, idx) => {
              const Icon = node.icon
              return (
                <div key={idx} className="flex items-center">
                  <motion.div className="w-28 flex flex-col items-center" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.08 }} viewport={{ once: true }}>
                    <div className={`w-14 h-14 rounded-full flex items-center justify-center border transition-all duration-300 ${idx === 0 ? 'bg-ds-accent-muted border-ds-accent/25 shadow-ds-glow' : 'bg-ds-card border-ds-border'}`}>
                      <Icon className="w-5 h-5 text-ds-accent" />
                    </div>
                    <p className="text-micro text-ds-text-secondary mt-3 text-center font-medium">{node.label[lang]}</p>
                  </motion.div>
                  {idx < pipelineNodes.length - 1 && (<ChevronRight className="w-4 h-4 text-ds-text-dim mx-1" />)}
                </div>
              )
            })}
          </div>
        </div>
      </motion.section>

      {/* MATHEMATICAL MODEL */}
      <motion.section className="ds-section bg-ds-bg-alt" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container">
          <SectionHeading tag={t('formulaTag', lang)} title={t('formulaTitle', lang)} subtitle={t('formulaSub', lang)} />
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="ds-card p-8 text-center">
              <div className="font-mono text-lg text-ds-accent mb-4">impact(node) = &Sigma;(edge_weight &times; source_impact) &times; sensitivity</div>
              <div className="font-mono text-sm text-ds-text-muted mb-2">effective_impact = impact &times; severity_modifier</div>
              <div className="font-mono text-sm text-ds-text-muted mb-2">E_total = &Sigma; impact_i&sup2;</div>
              <div className="font-mono text-sm text-ds-text-muted">normalized_i = impact_i / max(all node impacts)</div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="ds-card p-5">
                <div className="text-nano font-mono text-ds-accent-dim mb-2">{lang === 'ar' ? 'حدود التأثير' : 'IMPACT BOUNDS'}</div>
                <div className="font-mono text-ds-text text-sm">[-1.0, 1.0]</div>
                <div className="text-[10px] text-ds-text-dim mt-1">{lang === 'ar' ? 'مخمد بمعامل 0.3' : 'Dampened by 0.3 factor'}</div>
              </div>
              <div className="ds-card p-5">
                <div className="text-nano font-mono text-ds-accent-dim mb-2">{lang === 'ar' ? 'تكرارات BFS' : 'BFS ITERATIONS'}</div>
                <div className="font-mono text-ds-text text-sm">max 6</div>
                <div className="text-[10px] text-ds-text-dim mt-1">{lang === 'ar' ? 'عتبة &gt; 0.01' : 'Threshold > 0.01'}</div>
              </div>
              <div className="ds-card p-5">
                <div className="text-nano font-mono text-ds-accent-dim mb-2">{lang === 'ar' ? 'معادلة الثقة' : 'CONFIDENCE'}</div>
                <div className="font-mono text-ds-text text-sm">min(0.95, 0.6 + n&times;0.008)</div>
                <div className="text-[10px] text-ds-text-dim mt-1">{lang === 'ar' ? 'n = طول سلسلة الانتشار' : 'n = chain length'}</div>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      {/* 5-LAYER MODEL */}
      <motion.section className="ds-section bg-ds-bg" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container">
          <SectionHeading tag={t('layerTag', lang)} title={t('layerTitle', lang)} />
          <div className="max-w-3xl mx-auto space-y-4">
            {layers.map((layer, idx) => (
              <motion.div key={idx} className="ds-card p-5 flex items-start gap-4" initial={{ opacity: 0, x: -16 }} whileInView={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.08 }} viewport={{ once: true }}>
                <div className="w-3 h-3 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: layer.color }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-ds-text">{layer.name[lang]}</span>
                    <span className="text-[10px] font-mono text-ds-text-dim">{layer.count} {lang === 'ar' ? 'عقد' : 'nodes'}</span>
                  </div>
                  <p className="text-[11px] text-ds-text-muted">{layer.nodes[lang]}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* DEEP DIVE BLOCKS */}
      <motion.section className="ds-section bg-ds-bg-alt" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container">
          <SectionHeading tag={t('deepDive', lang)} title={t('archTitle', lang)} subtitle={t('archSub', lang)} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {archBlocks.map((block, idx) => {
              const Icon = block.icon
              return (
                <motion.div key={idx} className="ds-card p-8" initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.08, duration: 0.5 }} viewport={{ once: true }}>
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-nano font-mono text-ds-accent-dim">{block.step}</span>
                    <div className="w-10 h-10 rounded-ds bg-ds-accent-muted flex items-center justify-center"><Icon className="w-[18px] h-[18px] text-ds-accent" /></div>
                    <h3 className="text-h4 text-ds-text">{block.title[lang]}</h3>
                  </div>
                  <p className="text-caption text-ds-text-secondary leading-relaxed">{block.desc[lang]}</p>
                  <div className="mt-5 grid grid-cols-2 gap-2.5">
                    {block.features.map((feature, fidx) => (<div key={fidx} className="flex items-center gap-2 text-micro text-ds-text-muted"><div className="w-1 h-1 rounded-full bg-ds-accent-dim flex-shrink-0" />{feature[lang]}</div>))}
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      </motion.section>

      {/* TECH STACK */}
      <motion.section className="ds-section-tight bg-ds-bg" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container">
          <SectionHeading tag={t('stackTag', lang)} title={t('stackTitle', lang)} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <motion.div className="ds-card p-8" initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} viewport={{ once: true }}>
              <div className="flex items-center gap-2.5 mb-6"><Code2 className="w-5 h-5 text-ds-accent" /><h3 className="text-h4 text-ds-text">{t('frontend', lang)}</h3></div>
              <div className="flex flex-wrap gap-2.5">{frontendTechs.map((tech, idx) => (<span key={idx} className="text-micro px-3 py-1.5 bg-ds-surface-raised border border-ds-border rounded-ds text-ds-text-secondary">{tech}</span>))}</div>
            </motion.div>
            <motion.div className="ds-card p-8" initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} viewport={{ once: true }}>
              <div className="flex items-center gap-2.5 mb-6"><Terminal className="w-5 h-5 text-ds-accent" /><h3 className="text-h4 text-ds-text">{t('engine', lang)}</h3></div>
              <div className="flex flex-wrap gap-2.5">{engineTechs.map((tech, idx) => (<span key={idx} className="text-micro px-3 py-1.5 bg-ds-surface-raised border border-ds-border rounded-ds text-ds-text-secondary">{tech[lang]}</span>))}</div>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* CTA */}
      <motion.section className="ds-section-tight bg-ds-bg-alt" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container text-center">
          <motion.h2 className="text-h2 text-ds-text" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} viewport={{ once: true }}>{t('seeAction', lang)}</motion.h2>
          <motion.p className="text-body-lg text-ds-text-secondary mt-4 max-w-xl mx-auto" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} viewport={{ once: true }}>{t('seeActionDesc', lang)}</motion.p>
          <motion.div className="flex items-center justify-center gap-4 mt-10" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} viewport={{ once: true }}>
            <Link href="/demo" className="ds-btn-primary text-[15px] px-8 py-4">{t('launchSystem', lang)}</Link>
            <Link href="/" className="ds-btn-secondary text-[15px] px-8 py-4">{t('backHome', lang)}</Link>
          </motion.div>
        </div>
      </motion.section>

      <Footer />
    </div>
  )
}
