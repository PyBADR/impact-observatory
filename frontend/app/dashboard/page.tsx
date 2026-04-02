'use client'
import { useState, useEffect } from 'react'
import { getLanguage, type Language } from '@/lib/i18n'
import Navbar from '@/components/ui/Navbar'
import { scoreToColor, STATUS_LABELS, type DecisionStatus } from '@/lib/types/observatory'

/* ════════════════════════════════════════════════════
   Impact Observatory | مرصد الأثر — Executive Dashboard
   Financial-first. White boardroom. No clutter.
   Layout: Top KPIs → Financial Impact → Sector Stress → Decisions
   ════════════════════════════════════════════════════ */

const LABELS = {
  title:            { en: 'Impact Observatory', ar: 'مرصد الأثر' },
  subtitle:         { en: 'Decision Intelligence for Financial Impact', ar: 'ذكاء القرار لقياس الأثر المالي' },
  headline_loss:    { en: 'Headline Loss', ar: 'إجمالي الخسارة' },
  peak_day:         { en: 'Peak Impact Day', ar: 'يوم الذروة' },
  time_to_failure:  { en: 'Time to Failure', ar: 'وقت الانهيار' },
  severity:         { en: 'Severity', ar: 'الشدة' },
  financial_impact: { en: 'Financial Impact', ar: 'الأثر المالي' },
  banking_stress:   { en: 'Banking Stress', ar: 'ضغط القطاع البنكي' },
  insurance_stress: { en: 'Insurance Stress', ar: 'ضغط التأمين' },
  fintech_stress:   { en: 'Fintech Disruption', ar: 'اضطراب الفنتك' },
  decision_actions: { en: 'Recommended Actions', ar: 'الإجراءات المقترحة' },
  run_scenario:     { en: 'Run Scenario', ar: 'تشغيل السيناريو' },
  loading:          { en: 'Computing...', ar: 'جاري الحساب...' },
  no_data:          { en: 'Run a scenario to see results', ar: 'شغّل سيناريو لعرض النتائج' },
  hormuz:           { en: 'Hormuz Closure', ar: 'إغلاق هرمز' },
  confidence:       { en: 'Confidence', ar: 'الثقة' },
  liquidity_gap:    { en: 'Liquidity Gap', ar: 'فجوة السيولة' },
  capital_adequacy: { en: 'Capital Adequacy', ar: 'كفاية رأس المال' },
  claims_surge:     { en: 'Claims Surge', ar: 'ارتفاع المطالبات' },
  combined_ratio:   { en: 'Combined Ratio', ar: 'النسبة المجمعة' },
  payment_failure:  { en: 'Payment Failure Rate', ar: 'معدل فشل المدفوعات' },
  settlement_delay: { en: 'Settlement Delay', ar: 'تأخير التسوية' },
  duration:         { en: 'Duration', ar: 'المدة' },
  days:             { en: 'days', ar: 'يوم' },
  cost:             { en: 'Cost', ar: 'التكلفة' },
  avoids:           { en: 'Avoids', ar: 'تتجنب' },
  net_benefit:      { en: 'Net Benefit', ar: 'صافي الفائدة' },
  decision_plan:    { en: 'Decision Plan', ar: 'خطة القرارات' },
  regulatory:       { en: 'Regulatory', ar: 'التنظيمي' },
  sama:             { en: 'SAMA Alert', ar: 'تنبيه ساما' },
  triggers:         { en: 'Regulatory Triggers', ar: 'المحفزات التنظيمية' },
  entities:         { en: 'Entities', ar: 'الكيانات' },
  propagation:      { en: 'Propagation Steps', ar: 'خطوات الانتشار' },
}

function l(key: keyof typeof LABELS, lang: Language): string {
  return LABELS[key]?.[lang] || key
}

function severityClass(code: string): string {
  switch (code) {
    case 'CRITICAL': return 'ds-stress-critical'
    case 'HIGH': return 'ds-stress-high'
    case 'MEDIUM': return 'ds-stress-medium'
    default: return 'ds-stress-low'
  }
}

interface ObservatoryResult {
  schema_version?: string
  pipeline_stages_completed?: number
  financial_impact: {
    headline_loss_usd: number; peak_day: number; time_to_failure_days: number
    severity_code: string; confidence: number
  }
  banking_stress: {
    liquidity_gap_usd: number; capital_adequacy_ratio: number; interbank_rate_spike: number
    time_to_liquidity_breach_days: number; fx_reserve_drawdown_pct: number; stress_level: string
    stress_score: number
  }
  insurance_stress: {
    claims_surge_pct: number; reinsurance_trigger: boolean; combined_ratio: number
    solvency_margin_pct: number; time_to_insolvency_days: number; premium_adequacy: number
    stress_level: string; stress_score: number
  }
  fintech_stress: {
    payment_failure_rate: number; settlement_delay_hours: number; gateway_downtime_pct: number
    digital_banking_disruption: number; time_to_payment_failure_days: number; stress_level: string
    stress_score: number
  }
  decisions: {
    id: string; rank: number; title: string; title_ar: string; urgency: number; value: number
    priority: number; feasibility: number; time_effect: number; cost_usd: number
    loss_avoided_usd: number; regulatory_risk: number; sector: string; description: string
    status: string
  }[]
  decision_plan?: {
    name: string; name_ar: string; total_cost_usd: number; total_loss_avoided_usd: number
    net_benefit_usd: number; execution_days: number; sectors_covered: string[]
  }
  regulatory?: {
    pdpl_compliant: boolean; sama_alert_level: string; cbuae_alert_level: string
    regulatory_triggers: string[]; ifrs17_impact: number
  }
  entities?: { id: string; name: string; name_ar: string; layer: string }[]
  flow_states?: { timestep: number; total_stress: number; converged: boolean }[]
  explanation?: {
    summary_en: string; summary_ar: string
    key_findings: { en: string; ar: string }[]
  }
  audit_hash?: string
  computed_in_ms: number
  stage_timings?: Record<string, number>
}

function fmtUSD(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`
  return `$${v.toFixed(0)}`
}

export default function DashboardPage() {
  const [lang, setLangState] = useState<Language>('ar')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ObservatoryResult | null>(null)
  const [severity, setSeverity] = useState(0.85)
  const [duration, setDuration] = useState(14)
  const isRTL = lang === 'ar'

  useEffect(() => { setLangState(getLanguage()) }, [])

  const runScenario = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/v1/observatory/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: 'hormuz-closure-v1',
          name: 'Hormuz Strait Closure',
          name_ar: 'إغلاق مضيق هرمز',
          severity,
          duration_days: duration,
          description: `${duration}-day severe disruption of Hormuz Strait shipping corridor`,
        }),
      })
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const data = await res.json()
      setResult(data)
    } catch {
      setResult(computeClientPreview(severity, duration))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div dir={isRTL ? 'rtl' : 'ltr'} className="min-h-screen bg-ds-bg">
      <Navbar />
      <main className="ds-container pt-24 pb-16">

        {/* ── Header ── */}
        <div className="flex flex-col lg:flex-row items-start lg:items-end justify-between mb-10 gap-4">
          <div>
            <h1 className="text-h1 text-ds-text">{l('title', lang)}</h1>
            <p className="text-body text-ds-text-secondary mt-1">{l('subtitle', lang)}</p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-caption text-ds-text-secondary">{l('severity', lang)}</label>
              <input type="range" min="0.1" max="1.0" step="0.05" value={severity}
                onChange={e => setSeverity(parseFloat(e.target.value))}
                className="w-24 accent-ds-accent" />
              <span className="text-caption font-mono text-ds-text-muted w-10">{severity.toFixed(2)}</span>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-caption text-ds-text-secondary">{l('duration', lang)}</label>
              <input type="range" min="1" max="30" step="1" value={duration}
                onChange={e => setDuration(parseInt(e.target.value))}
                className="w-20 accent-ds-accent" />
              <span className="text-caption font-mono text-ds-text-muted w-10">{duration}d</span>
            </div>
            <button onClick={runScenario} disabled={loading} className="ds-btn-primary">
              {loading ? l('loading', lang) : `${l('run_scenario', lang)}: ${l('hormuz', lang)}`}
            </button>
          </div>
        </div>

        {!result ? (
          <div className="flex items-center justify-center h-96 text-ds-text-muted text-body-lg">
            {l('no_data', lang)}
          </div>
        ) : (
          <>
            {/* ── TOP: KPI Cards ── */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <KPICard label={l('headline_loss', lang)}
                value={fmtUSD(result.financial_impact.headline_loss_usd * 1e9)} sublabel="USD" large />
              <KPICard label={l('peak_day', lang)}
                value={`${isRTL ? 'اليوم' : 'Day'} ${result.financial_impact.peak_day}`} sublabel={`/ ${duration}`} />
              <KPICard label={l('time_to_failure', lang)}
                value={`${result.financial_impact.time_to_failure_days}`}
                sublabel={l('days', lang)} />
              <div className="ds-kpi flex flex-col items-center justify-center">
                <span className={`ds-badge text-caption font-bold px-4 py-2 ${severityClass(result.financial_impact.severity_code)}`}>
                  {result.financial_impact.severity_code}
                </span>
                <span className="ds-kpi-label mt-3">{l('severity', lang)}</span>
                <span className="ds-kpi-sublabel">{l('confidence', lang)}: {(result.financial_impact.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            {/* ── MIDDLE: Financial Impact + Sector Stress ── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
              {/* Financial Impact */}
              <div className="lg:col-span-2 ds-card p-6">
                <h2 className="text-h3 text-ds-text mb-5">{l('financial_impact', lang)}</h2>
                <div className="grid grid-cols-3 gap-6">
                  <MetricRow label={l('headline_loss', lang)} value={fmtUSD(result.financial_impact.headline_loss_usd * 1e9)} />
                  <MetricRow label={l('peak_day', lang)} value={`${isRTL ? 'اليوم' : 'Day'} ${result.financial_impact.peak_day}`} />
                  <MetricRow label={l('confidence', lang)} value={`${(result.financial_impact.confidence * 100).toFixed(0)}%`} />
                </div>

                {/* Regulatory info if available */}
                {result.regulatory && (
                  <div className="mt-6 pt-5 border-t border-ds-border">
                    <div className="flex items-center gap-4 flex-wrap">
                      <span className="text-caption text-ds-text-secondary font-medium">{l('sama', lang)}:</span>
                      <span className={`ds-badge text-nano font-bold ${severityClass(result.regulatory.sama_alert_level === 'CRITICAL' ? 'CRITICAL' : result.regulatory.sama_alert_level === 'WARNING' ? 'HIGH' : 'LOW')}`}>
                        {result.regulatory.sama_alert_level}
                      </span>
                      {result.regulatory.regulatory_triggers.length > 0 && (
                        <span className="text-micro text-ds-text-muted font-mono">
                          {result.regulatory.regulatory_triggers.length} {l('triggers', lang).toLowerCase()}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Sector Stress Stack */}
              <div className="flex flex-col gap-4">
                <SectorCard title={l('banking_stress', lang)} level={result.banking_stress.stress_level}
                  stressScore={result.banking_stress.stress_score}
                  metrics={[
                    { label: l('liquidity_gap', lang), value: fmtUSD(result.banking_stress.liquidity_gap_usd * 1e9) },
                    { label: l('capital_adequacy', lang), value: `${(result.banking_stress.capital_adequacy_ratio * 100).toFixed(1)}%` },
                  ]} />
                <SectorCard title={l('insurance_stress', lang)} level={result.insurance_stress.stress_level}
                  stressScore={result.insurance_stress.stress_score}
                  metrics={[
                    { label: l('claims_surge', lang), value: `+${result.insurance_stress.claims_surge_pct.toFixed(0)}%` },
                    { label: l('combined_ratio', lang), value: result.insurance_stress.combined_ratio.toFixed(2) },
                  ]} />
                <SectorCard title={l('fintech_stress', lang)} level={result.fintech_stress.stress_level}
                  stressScore={result.fintech_stress.stress_score}
                  metrics={[
                    { label: l('payment_failure', lang), value: `${(result.fintech_stress.payment_failure_rate * 100).toFixed(1)}%` },
                    { label: l('settlement_delay', lang), value: `${result.fintech_stress.settlement_delay_hours.toFixed(0)}h` },
                  ]} />
              </div>
            </div>

            {/* ── DECISION PLAN ── */}
            {result.decision_plan && (
              <div className="ds-card p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-h3 text-ds-text">{l('decision_plan', lang)}</h2>
                  <div className="flex items-center gap-4 text-caption">
                    <span className="text-ds-text-secondary">{l('net_benefit', lang)}:</span>
                    <span className="font-bold text-ds-success">{fmtUSD(result.decision_plan.net_benefit_usd)}</span>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-h4 text-ds-text">{fmtUSD(result.decision_plan.total_cost_usd)}</div>
                    <div className="text-micro text-ds-text-muted">{l('cost', lang)}</div>
                  </div>
                  <div>
                    <div className="text-h4 text-ds-success">{fmtUSD(result.decision_plan.total_loss_avoided_usd)}</div>
                    <div className="text-micro text-ds-text-muted">{l('avoids', lang)}</div>
                  </div>
                  <div>
                    <div className="text-h4 text-ds-text">{result.decision_plan.execution_days}d</div>
                    <div className="text-micro text-ds-text-muted">{l('duration', lang)}</div>
                  </div>
                  <div className="flex flex-wrap items-center justify-center gap-1">
                    {result.decision_plan.sectors_covered.map(s => (
                      <span key={s} className="ds-badge-accent text-nano">{s}</span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── BOTTOM: Decision Actions ── */}
            <div className="ds-card p-6 mb-6">
              <h2 className="text-h3 text-ds-text mb-4">{l('decision_actions', lang)}</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {result.decisions.map((d) => (
                  <div key={d.id} className="p-5 rounded-ds-lg border border-ds-border bg-ds-bg-alt">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-micro font-mono font-bold text-ds-accent">#{d.rank || '—'}</span>
                        <span className={`text-nano font-medium px-2 py-0.5 rounded-full ${
                          d.status === 'APPROVED' ? 'bg-green-100 text-green-700' :
                          d.status === 'EXECUTING' ? 'bg-blue-100 text-blue-700' :
                          'bg-amber-50 text-amber-700'
                        }`}>
                          {STATUS_LABELS[d.status as DecisionStatus]?.[isRTL ? 'ar' : 'en'] || d.status}
                        </span>
                      </div>
                      <span className="ds-badge-accent text-nano">{d.sector}</span>
                    </div>
                    <h3 className="text-h4 text-ds-text mb-1">{isRTL ? d.title_ar : d.title}</h3>
                    <p className="text-caption text-ds-text-secondary mb-3 line-clamp-2">{d.description}</p>
                    <div className="flex items-center justify-between text-micro text-ds-text-muted mb-2">
                      <span>{l('cost', lang)}: {fmtUSD(d.cost_usd)}</span>
                      <span>{l('avoids', lang)}: {fmtUSD(d.loss_avoided_usd)}</span>
                    </div>
                    <div className="flex items-center justify-between text-micro text-ds-text-muted mb-2">
                      <span>{isRTL ? 'الجدوى' : 'Feasibility'}: {(d.feasibility * 100).toFixed(0)}%</span>
                      <span>{isRTL ? 'فعالية الوقت' : 'Time Effect'}: {(d.time_effect * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-ds-surface rounded-full h-1.5">
                      <div className="bg-ds-accent h-1.5 rounded-full transition-all"
                        style={{ width: `${Math.min(100, d.priority * 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ── EXPLANATION (if available) ── */}
            {result.explanation && (
              <div className="ds-card p-6 mb-6">
                <h2 className="text-h3 text-ds-text mb-3">
                  {isRTL ? 'التفسير' : 'Explanation'}
                </h2>
                <p className="text-body text-ds-text-secondary leading-relaxed mb-4">
                  {isRTL ? result.explanation.summary_ar : result.explanation.summary_en}
                </p>
                {result.explanation.key_findings.length > 0 && (
                  <div className="space-y-2">
                    {result.explanation.key_findings.map((f, i) => (
                      <div key={i} className="flex items-start gap-2 text-caption text-ds-text-secondary">
                        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-ds-accent/10 text-ds-accent text-[10px] font-bold flex items-center justify-center mt-0.5">
                          {i + 1}
                        </span>
                        <span>{isRTL ? f.ar : f.en}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ── PROPAGATION METADATA (secondary) ── */}
            {(result.entities?.length || result.flow_states?.length) ? (
              <div className="grid grid-cols-2 gap-4 mb-6">
                {result.entities && result.entities.length > 0 && (
                  <div className="ds-card p-4">
                    <h3 className="text-h4 text-ds-text mb-2">{l('entities', lang)}</h3>
                    <div className="flex flex-wrap gap-1.5">
                      {result.entities.map(e => (
                        <span key={e.id} className="px-2 py-1 text-nano bg-ds-bg-alt border border-ds-border rounded-ds text-ds-text-secondary">
                          {isRTL ? e.name_ar : e.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {result.flow_states && result.flow_states.length > 0 && (
                  <div className="ds-card p-4">
                    <h3 className="text-h4 text-ds-text mb-2">{l('propagation', lang)}</h3>
                    <div className="flex items-end gap-1 h-12">
                      {result.flow_states.map((fs, i) => (
                        <div key={i}
                          className="bg-ds-accent/20 rounded-sm flex-1"
                          style={{ height: `${Math.min(100, (fs.total_stress / Math.max(1, ...result.flow_states!.map(s => s.total_stress))) * 100)}%` }}
                          title={`Step ${fs.timestep}: stress ${fs.total_stress.toFixed(3)}`}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}

            {/* ── FOOTER META ── */}
            <div className="flex items-center justify-between text-micro text-ds-text-dim font-mono">
              <span>
                {result.audit_hash ? `SHA-256: ${result.audit_hash.substring(0, 16)}...` : ''}
              </span>
              <div className="flex items-center gap-4">
                {result.pipeline_stages_completed != null && (
                  <span>{result.pipeline_stages_completed}/10 stages</span>
                )}
                {result.schema_version && (
                  <span>{result.schema_version}</span>
                )}
                <span>Computed in {result.computed_in_ms.toFixed(0)}ms</span>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

/* ── Sub-components ── */

function KPICard({ label, value, sublabel, large }: { label: string; value: string; sublabel?: string; large?: boolean }) {
  return (
    <div className="ds-kpi text-center">
      <div className={large ? 'text-display-sm font-bold text-ds-text' : 'text-h2 font-bold text-ds-text'}>{value}</div>
      <div className="ds-kpi-label">{label}</div>
      {sublabel && <div className="ds-kpi-sublabel">{sublabel}</div>}
    </div>
  )
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-h3 text-ds-text font-semibold">{value}</div>
      <div className="text-caption text-ds-text-secondary mt-0.5">{label}</div>
    </div>
  )
}

function SectorCard({ title, level, stressScore, metrics }: {
  title: string; level: string; stressScore?: number; metrics: { label: string; value: string }[]
}) {
  const gaugeColor = stressScore != null ? scoreToColor(stressScore) : undefined
  return (
    <div className="ds-card p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-h4 text-ds-text">{title}</span>
        <div className="flex items-center gap-2">
          {stressScore != null && (
            <span className="text-caption font-mono font-bold" style={{ color: gaugeColor }}>
              {stressScore.toFixed(1)}
            </span>
          )}
          <span className={`ds-badge text-nano font-bold ${severityClass(level.toUpperCase())}`}>{level}</span>
        </div>
      </div>
      {stressScore != null && (
        <div className="w-full bg-ds-surface rounded-full h-1.5 mb-3">
          <div className="h-1.5 rounded-full transition-all" style={{
            width: `${Math.min(100, stressScore)}%`,
            backgroundColor: gaugeColor,
          }} />
        </div>
      )}
      <div className="space-y-2">
        {metrics.map(m => (
          <div key={m.label} className="flex items-center justify-between">
            <span className="text-caption text-ds-text-secondary">{m.label}</span>
            <span className="text-caption font-mono font-semibold text-ds-text">{m.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── Client-side preview when API is unavailable ── */
function computeClientPreview(severity: number, duration: number): ObservatoryResult {
  const gccGDP = 2100, gdpMultiplier = 0.65, bankingAssets = 2800, insSpike = 1.5
  const headlineLoss = gccGDP * (1 - gdpMultiplier) * severity * (duration / 14)
  const peakDay = Math.min(duration, Math.max(3, Math.round(duration * 0.5)))
  const ttf = Math.max(1, Math.round(14 / severity))

  let severityCode = 'LOW'
  if (headlineLoss >= 500) severityCode = 'CRITICAL'
  else if (headlineLoss >= 200) severityCode = 'HIGH'
  else if (headlineLoss >= 50) severityCode = 'MEDIUM'

  const liqGap = bankingAssets * 0.03 * severity * (duration / 14)
  const car = Math.max(0.08, 0.18 - (0.10 * severity))
  const claimsSurge = insSpike * 100 * severity - 100
  const combinedRatio = 0.95 + (0.35 * severity)
  const paymentFailure = Math.min(0.15, 0.02 + (0.13 * severity))
  const settlementDelay = 4 + (72 * severity)

  const bankLevel = car < 0.10 ? 'CRITICAL' : car < 0.12 ? 'HIGH' : car < 0.15 ? 'MEDIUM' : 'LOW'
  const insLevel = combinedRatio > 1.25 ? 'CRITICAL' : combinedRatio > 1.15 ? 'HIGH' : combinedRatio > 1.05 ? 'MEDIUM' : 'LOW'
  const finLevel = paymentFailure > 0.10 ? 'CRITICAL' : paymentFailure > 0.07 ? 'HIGH' : paymentFailure > 0.04 ? 'MEDIUM' : 'LOW'

  // Stress scores (0-100): Banking = 50% CAR + 30% liquidity + 20% interbank
  const interbankSpike = 0.5 + (2.5 * severity)
  const bankStressScore = Math.min(100, (
    0.50 * Math.min(100, ((0.18 - car) / 0.10) * 100) +
    0.30 * Math.min(100, (liqGap / (bankingAssets * 0.03)) * 100) +
    0.20 * Math.min(100, (interbankSpike / 3.0) * 100)
  ))
  // Insurance = 40% solvency + 35% CR + 25% claims
  const solMargin = Math.max(5, 40 - (35 * severity))
  const insStressScore = Math.min(100, (
    0.40 * Math.min(100, ((40 - solMargin) / 35) * 100) +
    0.35 * Math.min(100, ((combinedRatio - 0.95) / 0.55) * 100) +
    0.25 * Math.min(100, (claimsSurge / 50) * 100)
  ))
  // Fintech = 40% PFR + 35% gateway + 25% disruption
  const gatewayDown = Math.min(25, 2 + (23 * severity))
  const digDisruption = Math.min(0.8, 0.05 + (0.75 * severity))
  const finStressScore = Math.min(100, (
    0.40 * Math.min(100, (paymentFailure / 0.15) * 100) +
    0.35 * Math.min(100, (gatewayDown / 25) * 100) +
    0.25 * Math.min(100, (digDisruption / 0.8) * 100)
  ))

  return {
    schema_version: 'v1',
    pipeline_stages_completed: 10,
    financial_impact: {
      headline_loss_usd: headlineLoss, peak_day: peakDay,
      time_to_failure_days: ttf, severity_code: severityCode, confidence: 0.78,
    },
    banking_stress: {
      liquidity_gap_usd: liqGap, capital_adequacy_ratio: car,
      interbank_rate_spike: interbankSpike,
      time_to_liquidity_breach_days: Math.max(1, Math.round(30 / (severity * 2))),
      fx_reserve_drawdown_pct: Math.min(25, 5 * severity), stress_level: bankLevel,
      stress_score: bankStressScore,
    },
    insurance_stress: {
      claims_surge_pct: claimsSurge, reinsurance_trigger: claimsSurge > 30,
      combined_ratio: combinedRatio, solvency_margin_pct: solMargin,
      time_to_insolvency_days: Math.max(1, Math.round(60 / (severity * 2))),
      premium_adequacy: Math.max(0.3, 1.0 - (0.7 * severity)), stress_level: insLevel,
      stress_score: insStressScore,
    },
    fintech_stress: {
      payment_failure_rate: paymentFailure, settlement_delay_hours: settlementDelay,
      gateway_downtime_pct: gatewayDown, digital_banking_disruption: digDisruption,
      time_to_payment_failure_days: Math.max(1, Math.round(21 / (severity * 1.5))),
      stress_level: finLevel, stress_score: finStressScore,
    },
    decisions: [
      {
        id: 'act-001', rank: 1, title: 'Emergency Liquidity Facility', title_ar: 'تسهيل سيولة طارئ',
        urgency: 0.92, value: 0.88, priority: 0.91, feasibility: 0.85, time_effect: 0.92,
        cost_usd: 2.5e9, loss_avoided_usd: 45e9, regulatory_risk: 0.15, sector: 'banking',
        description: 'Activate GCC central bank emergency liquidity window for systemically important banks.',
        status: 'PENDING_REVIEW',
      },
      {
        id: 'act-002', rank: 2, title: 'Payment System Backup Activation', title_ar: 'تفعيل نظام مدفوعات احتياطي',
        urgency: 0.88, value: 0.85, priority: 0.82, feasibility: 0.78, time_effect: 0.88,
        cost_usd: 350e6, loss_avoided_usd: 8e9, regulatory_risk: 0.10, sector: 'fintech',
        description: 'Deploy backup payment routing through SWIFT alternatives and regional settlement override.',
        status: 'PENDING_REVIEW',
      },
      {
        id: 'act-003', rank: 3, title: 'Reinsurance Treaty Activation', title_ar: 'تفعيل اتفاقية إعادة التأمين',
        urgency: 0.82, value: 0.78, priority: 0.76, feasibility: 0.72, time_effect: 0.81,
        cost_usd: 800e6, loss_avoided_usd: 12e9, regulatory_risk: 0.12, sector: 'insurance',
        description: 'Trigger catastrophe reinsurance treaties to absorb marine and cargo claims surge.',
        status: 'PENDING_REVIEW',
      },
    ],
    decision_plan: {
      name: 'Response Plan: Hormuz Closure',
      name_ar: 'خطة الاستجابة: إغلاق هرمز',
      total_cost_usd: 3.65e9, total_loss_avoided_usd: 65e9, net_benefit_usd: 61.35e9,
      execution_days: 7, sectors_covered: ['banking', 'fintech', 'insurance'],
    },
    regulatory: {
      pdpl_compliant: true, sama_alert_level: 'CRITICAL', cbuae_alert_level: 'CRITICAL',
      regulatory_triggers: ['IFRS17_LOSS_RECOGNITION', 'BASEL3_CONSERVATION_BUFFER_WARNING', 'SAMA_ALERT_CRITICAL'],
      ifrs17_impact: 42.5,
    },
    computed_in_ms: 1.4,
  }
}
