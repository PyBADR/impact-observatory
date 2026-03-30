'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Search, Globe, Filter, ChevronRight, Layers } from 'lucide-react'
import Link from 'next/link'
import { gccScenarios, gccNodes, layerMeta, type GCCLayer } from '@/lib/gcc-graph'
import { getLanguage, type Language } from '@/lib/i18n'

const SL: Record<string, { en: string; ar: string }> = {
  title: { en: 'Scenario Library', ar: 'مكتبة السيناريوهات' },
  subtitle: { en: 'GCC risk scenarios powered by the 5-layer causal graph', ar: 'سيناريوهات مخاطر خليجية مدعومة بالرسم السببي ذي الطبقات الخمس' },
  openRoom: { en: 'Open Control Room', ar: 'فتح غرفة التحكم' },
  search: { en: 'Search scenarios...', ar: 'بحث في السيناريوهات...' },
  all: { en: 'All', ar: 'الكل' },
  shocks: { en: 'Shock Nodes', ar: 'عقد الصدمة' },
  launch: { en: 'Launch', ar: 'تشغيل' },
  noMatch: { en: 'No scenarios match your filter', ar: 'لا توجد سيناريوهات تطابق الفلتر' },
  of: { en: 'of', ar: 'من' },
  scenarios: { en: 'scenarios', ar: 'سيناريوهات' },
}

function t(key: string, lang: Language): string {
  return SL[key]?.[lang] || key
}

const categoryColors: Record<string, string> = {
  economy: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  finance: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  infrastructure: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  society: 'text-red-400 bg-red-500/10 border-red-500/20',
  'business reaction': 'text-orange-400 bg-orange-500/10 border-orange-500/20',
}

export default function ScenariosPage() {
  const [lang, setLang] = useState<Language>('ar')
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  useEffect(() => { setLang(getLanguage()) }, [])

  const categories = ['all', ...new Set(gccScenarios.map(s => s.category))]

  const filtered = gccScenarios.filter(s => {
    if (filter !== 'all' && s.category !== filter) return false
    if (search) {
      const q = search.toLowerCase()
      return s.title.toLowerCase().includes(q) || s.titleAr.includes(search) || s.description.toLowerCase().includes(q)
    }
    return true
  })

  return (
    <div className="min-h-screen bg-ds-bg text-ds-text" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
      <header className="h-14 border-b border-zinc-800/60 flex items-center justify-between px-6 bg-zinc-950/80 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-zinc-500 hover:text-zinc-300 transition-colors"><ArrowLeft className="w-4 h-4" /></Link>
          <span className="text-xs font-mono font-bold tracking-wider text-cyan-400">{lang === 'ar' ? 'ديفو سيم' : 'DEEVO SIM'}</span>
          <span className="text-zinc-600">/</span>
          <span className="text-xs text-zinc-400">{t('title', lang)}</span>
        </div>
        <Link href="/demo" className="text-xs px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white transition-colors">
          {t('openRoom', lang)}
        </Link>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-100 mb-2">{t('title', lang)}</h1>
          <p className="text-sm text-zinc-500">{t('subtitle', lang)}</p>
        </div>

        <div className="flex items-center gap-4 mb-6 flex-wrap">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder={t('search', lang)} className="w-full bg-zinc-900 border border-zinc-800 rounded-lg ps-10 pe-4 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none focus:border-cyan-500/40" />
          </div>
          <div className="flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-zinc-500 me-1" />
            {categories.map(d => (
              <button key={d} onClick={() => setFilter(d)} className={`text-[10px] uppercase tracking-wider px-2.5 py-1.5 rounded-md transition-all ${filter === d ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30' : 'text-zinc-500 hover:text-zinc-400 border border-transparent'}`}>
                {d === 'all' ? t('all', lang) : d}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((sc, i) => (
            <motion.div key={sc.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
              className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition-all group cursor-pointer">
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg border ${categoryColors[sc.category] || 'text-zinc-400 bg-zinc-800 border-zinc-700'}`}>
                  <Layers className="w-4 h-4" />
                </div>
                <span className="text-[10px] font-mono text-zinc-500">{sc.country}</span>
              </div>
              <h3 className="text-sm font-semibold text-zinc-100 mb-1 group-hover:text-cyan-300 transition-colors">
                {lang === 'ar' ? sc.titleAr : sc.title}
              </h3>
              <p className="text-xs text-zinc-400 leading-relaxed mb-4 line-clamp-2">
                {lang === 'ar' ? sc.descriptionAr : sc.description}
              </p>
              <div className="mb-3">
                <span className="text-[10px] text-zinc-600 uppercase tracking-wider">{t('shocks', lang)}</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {sc.shocks.map(shock => {
                    const node = gccNodes.find(n => n.id === shock.nodeId)
                    const layer = node?.layer || 'geography'
                    return (
                      <span key={shock.nodeId} className="text-[10px] px-2 py-0.5 rounded border" style={{ color: layerMeta[layer as GCCLayer]?.color, borderColor: layerMeta[layer as GCCLayer]?.color + '30', backgroundColor: layerMeta[layer as GCCLayer]?.color + '10' }}>
                        {lang === 'ar' ? (node?.labelAr || node?.label) : node?.label} ({(shock.impact * 100).toFixed(0)}%)
                      </span>
                    )
                  })}
                </div>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-zinc-800/60">
                <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded ${categoryColors[sc.category] || ''}`}>{sc.category}</span>
                <Link href={`/demo?scenario=${sc.id}`} className="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                  {t('launch', lang)} <ChevronRight className="w-3 h-3" />
                </Link>
              </div>
            </motion.div>
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-16">
            <Globe className="w-8 h-8 text-zinc-700 mx-auto mb-3" />
            <p className="text-sm text-zinc-500">{t('noMatch', lang)}</p>
          </div>
        )}

        <div className="mt-8 text-center">
          <p className="text-[10px] uppercase tracking-widest text-zinc-600">{filtered.length} {t('of', lang)} {gccScenarios.length} {t('scenarios', lang)}</p>
        </div>
      </div>
    </div>
  )
}
