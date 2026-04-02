'use client'
import Link from 'next/link'
import { getLanguage, type Language } from '@/lib/i18n'
import { useState, useEffect } from 'react'

const FL: Record<string, { en: string; ar: string }> = {
  dashboard: { en: 'Dashboard', ar: 'لوحة القيادة' },
  scenarios: { en: 'Scenarios', ar: 'السيناريوهات' },
  decisions: { en: 'Decisions', ar: 'القرارات' },
  reports: { en: 'Reports', ar: 'التقارير' },
  rights: { en: 'Impact Observatory', ar: 'مرصد الأثر' },
}

export default function Footer() {
  const [lang, setLang] = useState<Language>('ar')
  useEffect(() => { setLang(getLanguage()) }, [])
  const currentYear = new Date().getFullYear()
  const t = (k: string) => FL[k]?.[lang] || k

  return (
    <footer className="border-t border-ds-border bg-ds-bg" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
      <div className="ds-container py-16">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-ds bg-ds-accent/12 border border-ds-accent/20 flex items-center justify-center">
              <span className="text-ds-accent font-bold text-xs">IO</span>
            </div>
            <span className="text-ds-text font-semibold tracking-tight">{lang === 'ar' ? 'مرصد الأثر' : 'Impact Observatory'}</span>
          </div>
          <nav className="flex items-center gap-8 text-[13px] text-ds-text-secondary">
            <Link href="/dashboard" className="hover:text-ds-text transition-colors duration-200">{t('dashboard')}</Link>
            <Link href="/scenarios" className="hover:text-ds-text transition-colors duration-200">{t('scenarios')}</Link>
            <Link href="/decisions" className="hover:text-ds-text transition-colors duration-200">{t('decisions')}</Link>
            <Link href="/reports" className="hover:text-ds-text transition-colors duration-200">{t('reports')}</Link>
          </nav>
          <p className="text-micro text-ds-text-dim">
            &copy; {currentYear} {t('rights')}
          </p>
        </div>
      </div>
    </footer>
  )
}
