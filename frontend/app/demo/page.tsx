'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  RotateCcw,
  Zap,
  Globe,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  Circle,
  Clock,
  Activity,
  Radio,
  Shield,
  BarChart3,
  Languages,
  Network,
} from 'lucide-react'

import GraphPanel from '@/components/graph/GraphPanel'
import GlobePanel from '@/components/globe/GlobePanel'
import TimelinePanel from '@/components/simulation/TimelinePanel'
import ReportPanel from '@/components/report/ReportPanel'
import ChatPanel from '@/components/chat/ChatPanel'
import { ImpactChainPanel, TopDriversPanel, SectorImpactPanel, ExplanationPanel } from '@/components/panels/PropagationPanels'

import { gccNodes, gccEdges, gccScenarios, gccNodesToGraphNodes, gccEdgesToGraphEdges } from '@/lib/gcc-graph'
import { runPropagation, type PropagationResult } from '@/lib/propagation-engine'
import { mockSimulationSteps, mockChatMessages } from '@/lib/mock-data'
import { setLanguage, getLanguage, label, type Language } from '@/lib/i18n'

/* ──────────────────────────────────────────────
   Processing pipeline steps (bilingual)
   ────────────────────────────────────────────── */
const processingSteps = [
  { en: 'Parsing scenario input', ar: 'تحليل مدخلات السيناريو' },
  { en: 'Extracting entities', ar: 'استخراج الكيانات' },
  { en: 'Building causal graph', ar: 'بناء الرسم البياني السببي' },
  { en: 'Running propagation engine', ar: 'تشغيل محرك الانتشار' },
  { en: 'Computing sector impacts', ar: 'حساب تأثيرات القطاعات' },
  { en: 'Generating intelligence brief', ar: 'إنشاء الموجز الاستخباراتي' },
]

/* ──────────────────────────────────────────────
   View mode type
   ────────────────────────────────────────────── */
type ViewMode = 'graph' | 'globe'

export default function DemoPage() {
  // ── Language ──
  const [lang, setLang] = useState<Language>('ar')

  useEffect(() => {
    setLanguage(lang)
  }, [lang])

  const toggleLang = useCallback(() => {
    setLang(prev => prev === 'ar' ? 'en' : 'ar')
  }, [])

  // ── State ──
  const [selectedScenarioId, setSelectedScenarioId] = useState(gccScenarios[0].id)
  const [isRunning, setIsRunning] = useState(false)
  const [hasResults, setHasResults] = useState(false)
  const [processingStep, setProcessingStep] = useState(0)
  const [isMobile, setIsMobile] = useState(false)
  const [runId, setRunId] = useState('—')
  const [runTimestamp, setRunTimestamp] = useState('—')
  const [viewMode, setViewMode] = useState<ViewMode>('graph')
  const [currentStep, setCurrentStep] = useState(0)

  // ── Propagation result ──
  const [propagationResult, setPropagationResult] = useState<PropagationResult | null>(null)

  const selectedScenario = useMemo(
    () => gccScenarios.find(s => s.id === selectedScenarioId) ?? gccScenarios[0],
    [selectedScenarioId]
  )

  // ── Graph data from propagation ──
  const graphNodes = useMemo(() => {
    const base = gccNodesToGraphNodes(gccNodes)
    if (!propagationResult) return base
    return base.map(n => ({
      ...n,
      weight: Math.max(n.weight, Math.abs(propagationResult.nodeImpacts.get(n.id) ?? 0)),
    }))
  }, [propagationResult])

  const graphEdges = useMemo(() => gccEdgesToGraphEdges(gccEdges), [])

  // ── System energy for normalized impacts ──
  const systemEnergy = useMemo(() => {
    if (!propagationResult) return 1
    let total = 0
    for (const v of propagationResult.nodeImpacts.values()) total += Math.abs(v)
    return Math.max(total, 1)
  }, [propagationResult])

  // ── Mobile detection ──
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 1024)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // ── Simulation processing animation ──
  useEffect(() => {
    if (!isRunning) return
    const interval = setInterval(() => {
      setProcessingStep(prev => {
        if (prev < processingSteps.length - 1) return prev + 1
        return prev
      })
    }, 600)
    return () => clearInterval(interval)
  }, [isRunning])

  useEffect(() => {
    if (processingStep === processingSteps.length - 1 && isRunning) {
      const timeout = setTimeout(() => {
        // Run REAL propagation engine
        const result = runPropagation(gccNodes, gccEdges, selectedScenario.shocks)
        setPropagationResult(result)
        setIsRunning(false)
        setHasResults(true)
        setCurrentStep(0)
      }, 400)
      return () => clearTimeout(timeout)
    }
  }, [processingStep, isRunning, selectedScenario])

  // ── Handlers ──
  const handleScenarioSelect = (scenarioId: string) => {
    setSelectedScenarioId(scenarioId)
    setHasResults(false)
    setCurrentStep(0)
    setPropagationResult(null)
  }

  const handleReset = () => {
    setHasResults(false)
    setCurrentStep(0)
    setProcessingStep(0)
    setIsRunning(false)
    setRunId('—')
    setRunTimestamp('—')
    setPropagationResult(null)
  }

  const handleRunSimulation = () => {
    setIsRunning(true)
    setProcessingStep(0)
    setHasResults(false)
    setPropagationResult(null)
    setRunId(`SIM-${Math.random().toString(36).substring(2, 8).toUpperCase()}`)
    setRunTimestamp(new Date().toLocaleTimeString('en-US', { hour12: false }))
  }

  // ── System status ──
  const systemStatus = useMemo(() => {
    if (isRunning) return { label: lang === 'ar' ? 'جارٍ المعالجة' : 'PROCESSING', color: 'bg-ds-accent', pulse: true }
    if (hasResults) return { label: lang === 'ar' ? 'مكتمل' : 'COMPLETE', color: 'bg-ds-success', pulse: false }
    return { label: lang === 'ar' ? 'جاهز' : 'READY', color: 'bg-ds-text-dim', pulse: false }
  }, [isRunning, hasResults, lang])

  // ── Mobile fallback ──
  if (isMobile) {
    return (
      <div className="h-screen w-full bg-ds-bg flex items-center justify-center p-6">
        <div className="ds-card p-10 text-center max-w-md">
          <div className="w-14 h-14 rounded-full bg-ds-surface-raised border border-ds-border flex items-center justify-center mx-auto mb-5">
            <Globe className="w-6 h-6 text-ds-text-muted" />
          </div>
          <h2 className="text-h3 mb-3">{lang === 'ar' ? 'مطلوب سطح المكتب' : 'Desktop Required'}</h2>
          <p className="text-caption text-ds-text-muted mb-8 leading-relaxed">
            {lang === 'ar' ? 'غرفة التحكم تتطلب شاشة سطح المكتب للتجربة الكاملة.' : 'The Control Room requires a desktop viewport for the full intelligence experience.'}
          </p>
          <Link href="/" className="ds-btn-primary">
            <ArrowLeft className="w-4 h-4" />
            {lang === 'ar' ? 'العودة' : 'Back to Home'}
          </Link>
        </div>
      </div>
    )
  }

  /* ══════════════════════════════════════════════
     MAIN SYSTEM INTERFACE
     ══════════════════════════════════════════════ */
  return (
    <div className="h-screen w-full bg-ds-bg flex flex-col overflow-hidden" dir={lang === 'ar' ? 'rtl' : 'ltr'}>

      {/* ── TOP BAR — System status bar ── */}
      <div className="h-11 border-b border-ds-border bg-ds-surface/80 backdrop-blur-xl flex-shrink-0 flex items-center justify-between px-5">
        {/* Left: Nav + breadcrumb */}
        <div className="flex items-center gap-3 min-w-0">
          <Link href="/" className="flex items-center gap-2 text-ds-text-muted hover:text-ds-text transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
          </Link>
          <div className="w-px h-5 bg-ds-border" />
          <span className="text-micro font-semibold text-ds-text tracking-tight">DEEVO SIM</span>
          <span className="text-micro text-ds-text-dim font-mono">/</span>
          <span className="text-micro text-ds-text-muted font-mono">
            {lang === 'ar' ? 'غرفة التحكم' : 'Control Room'}
          </span>
        </div>

        {/* Center: System status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${systemStatus.color} ${systemStatus.pulse ? 'animate-pulse' : ''}`} />
            <span className="text-nano font-mono uppercase tracking-[0.15em] text-ds-text-secondary">
              {systemStatus.label}
            </span>
          </div>
          {runId !== '—' && (
            <>
              <span className="text-nano text-ds-text-dim">·</span>
              <span className="text-nano font-mono text-ds-text-dim">
                <Clock size={10} className="inline mr-1 -mt-0.5" />
                {runTimestamp}
              </span>
              <span className="text-nano font-mono text-ds-text-dim">{runId}</span>
            </>
          )}
        </div>

        {/* Right: Language toggle + Mode + Status */}
        <div className="flex items-center gap-3 min-w-0">
          {/* Language toggle */}
          <button
            onClick={toggleLang}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-ds-card border border-ds-border hover:border-ds-border-hover transition-all"
          >
            <Languages size={10} className="text-ds-text-muted" />
            <span className="text-nano font-mono text-ds-text-muted">{lang === 'ar' ? 'EN' : 'عربي'}</span>
          </button>

          {/* View toggle */}
          {hasResults && (
            <div className="flex items-center rounded-full bg-ds-card border border-ds-border overflow-hidden">
              <button
                onClick={() => setViewMode('graph')}
                className={`flex items-center gap-1 px-2 py-0.5 text-nano font-mono transition-colors ${viewMode === 'graph' ? 'bg-ds-accent/15 text-ds-accent' : 'text-ds-text-dim hover:text-ds-text-muted'}`}
              >
                <Network size={10} />
                {lang === 'ar' ? 'رسم' : 'Graph'}
              </button>
              <button
                onClick={() => setViewMode('globe')}
                className={`flex items-center gap-1 px-2 py-0.5 text-nano font-mono transition-colors ${viewMode === 'globe' ? 'bg-ds-accent/15 text-ds-accent' : 'text-ds-text-dim hover:text-ds-text-muted'}`}
              >
                <Globe size={10} />
                {lang === 'ar' ? 'كرة' : 'Globe'}
              </button>
            </div>
          )}

          {/* Engine status */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-nano font-mono text-emerald-400 tracking-wider">
              {lang === 'ar' ? 'محرك حي' : 'ENGINE LIVE'}
            </span>
          </div>

          <span className="text-micro text-ds-text-muted truncate max-w-[200px] font-mono">
            {lang === 'ar' ? selectedScenario.titleAr : selectedScenario.title}
          </span>
        </div>
      </div>

      {/* ── MAIN 3-COLUMN LAYOUT ── */}
      <div className="flex-1 flex overflow-hidden">

        {/* ═══ LEFT SIDEBAR — Controls ═══ */}
        <div className="w-[280px] bg-ds-surface border-r border-ds-border overflow-y-auto flex flex-col" style={{ borderRight: lang === 'ar' ? 'none' : undefined, borderLeft: lang === 'ar' ? '1px solid var(--ds-border)' : undefined }}>
          <div className="p-5 space-y-5 flex flex-col">

            {/* Scenario Input */}
            <div>
              <h3 className="text-nano uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-3 flex items-center gap-2">
                <Radio size={10} />
                {lang === 'ar' ? 'إدخال السيناريو' : 'Scenario Input'}
              </h3>
              <div className="space-y-3">
                <div className="ds-card rounded-ds-lg p-3 border border-ds-accent/20">
                  <div className="text-micro font-medium text-ds-text mb-1">
                    {lang === 'ar' ? selectedScenario.titleAr : selectedScenario.title}
                  </div>
                  <p className="text-[10px] text-ds-text-muted leading-relaxed" dir="auto">
                    {lang === 'ar' ? selectedScenario.descriptionAr : selectedScenario.description}
                  </p>
                  <div className="flex items-center gap-2 mt-2 text-[9px] font-mono text-ds-text-dim">
                    <span>{selectedScenario.country}</span>
                    <span>·</span>
                    <span>{selectedScenario.category}</span>
                    <span>·</span>
                    <span>{selectedScenario.shocks.length} {lang === 'ar' ? 'صدمات' : 'shocks'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunSimulation}
              disabled={isRunning}
              className="w-full ds-btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {lang === 'ar' ? 'جارٍ المعالجة...' : 'Processing...'}
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  {lang === 'ar' ? 'تشغيل المحاكاة' : 'Run Simulation'}
                </>
              )}
            </button>

            {/* Processing Pipeline */}
            <AnimatePresence>
              {isRunning && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="pt-4 border-t border-ds-border space-y-3">
                    <h3 className="text-nano uppercase tracking-[0.15em] text-ds-text-dim font-semibold flex items-center gap-2">
                      <Activity size={10} className="text-ds-accent" />
                      {lang === 'ar' ? 'خط الأنابيب' : 'Pipeline'}
                    </h3>
                    <div className="space-y-2.5">
                      {processingSteps.map((step, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: lang === 'ar' ? 8 : -8 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="flex items-center gap-2.5"
                        >
                          {idx < processingStep ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-ds-success flex-shrink-0" />
                          ) : idx === processingStep ? (
                            <Loader2 className="w-3.5 h-3.5 text-ds-accent animate-spin flex-shrink-0" />
                          ) : (
                            <Circle className="w-3.5 h-3.5 text-ds-text-dim flex-shrink-0" />
                          )}
                          <span className={`text-[11px] font-mono ${
                            idx < processingStep
                              ? 'text-ds-text-muted line-through'
                              : idx === processingStep
                                ? 'text-ds-accent'
                                : 'text-ds-text-dim'
                          }`}>
                            {lang === 'ar' ? step.ar : step.en}
                          </span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Divider */}
            <div className="ds-divider" />

            {/* GCC Scenario Library */}
            <div>
              <h3 className="text-nano uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-3 flex items-center gap-2">
                <Shield size={10} />
                {lang === 'ar' ? 'مكتبة السيناريوهات' : 'GCC Scenarios'}
              </h3>
              <div className="space-y-2">
                {gccScenarios.map((scenario) => (
                  <button
                    key={scenario.id}
                    onClick={() => handleScenarioSelect(scenario.id)}
                    className={`w-full text-left px-3.5 py-3 rounded-ds-lg border transition-all duration-200 ${
                      selectedScenarioId === scenario.id
                        ? 'bg-ds-accent/8 border-ds-accent/25'
                        : 'bg-ds-bg-alt border-ds-border hover:border-ds-border-hover hover:bg-ds-card/40'
                    }`}
                    dir={lang === 'ar' ? 'rtl' : 'ltr'}
                  >
                    <div className="text-micro font-medium text-ds-text truncate">
                      {lang === 'ar' ? scenario.titleAr : scenario.title}
                    </div>
                    <div className="flex items-center gap-1.5 mt-1.5 text-[10px] text-ds-text-dim font-mono">
                      <Globe className="w-3 h-3" />
                      {scenario.country}
                      <span>·</span>
                      <span>{scenario.shocks.length} {lang === 'ar' ? 'صدمات' : 'shocks'}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ═══ CENTER — Graph/Globe + Timeline ═══ */}
        <div className="flex-1 bg-ds-bg overflow-y-auto flex flex-col p-4 gap-4">
          {/* Graph/Globe Panel — dominant visual weight */}
          <div className="flex-1 min-h-[420px]">
            {!hasResults && !isRunning && (
              <div className="h-full ds-card rounded-ds-xl flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 ds-grid-bg opacity-20" />
                <div className="relative text-center">
                  <div className="w-12 h-12 rounded-full bg-ds-surface-raised border border-ds-border flex items-center justify-center mx-auto mb-3">
                    <Circle className="w-5 h-5 text-ds-text-dim" />
                  </div>
                  <p className="text-caption text-ds-text-dim">
                    {lang === 'ar' ? 'قم بتشغيل المحاكاة لتوليد الرسم البياني' : 'Run a simulation to generate the causal graph'}
                  </p>
                  <p className="text-nano text-ds-text-dim mt-1 font-mono">
                    {lang === 'ar' ? 'في انتظار الإدخال' : 'AWAITING INPUT'}
                  </p>
                  <p className="text-[9px] text-ds-text-dim mt-3 font-mono">
                    {gccNodes.length} {lang === 'ar' ? 'كيان' : 'entities'} · {gccEdges.length} {lang === 'ar' ? 'علاقة' : 'edges'} · 5 {lang === 'ar' ? 'طبقات' : 'layers'}
                  </p>
                </div>
              </div>
            )}
            {isRunning && (
              <div className="h-full ds-card rounded-ds-xl flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 ds-grid-bg opacity-20" />
                <div className="relative text-center">
                  <Loader2 className="w-10 h-10 mx-auto mb-3 text-ds-accent animate-spin" />
                  <p className="text-caption text-ds-text-muted">
                    {lang === 'ar' ? 'جارٍ حساب الانتشار السببي...' : 'Computing causal propagation...'}
                  </p>
                  <p className="text-nano text-ds-accent font-mono mt-1">
                    {lang === 'ar' ? 'الانتشار نشط' : 'PROPAGATION ACTIVE'}
                  </p>
                </div>
              </div>
            )}
            {hasResults && viewMode === 'graph' && (
              <GraphPanel initialNodes={graphNodes} initialEdges={graphEdges} />
            )}
            {hasResults && viewMode === 'globe' && propagationResult && (
              <GlobePanel
                nodes={gccNodes}
                edges={gccEdges}
                nodeImpacts={propagationResult.nodeImpacts}
                systemEnergy={systemEnergy}
              />
            )}
          </div>

          {/* Timeline Panel */}
          <div className="flex-shrink-0">
            {!hasResults && !isRunning && (
              <div className="ds-card rounded-ds-xl p-5 text-center">
                <p className="text-caption text-ds-text-dim font-mono">
                  {lang === 'ar' ? 'الجدول الزمني · في انتظار المحاكاة' : 'TIMELINE · AWAITING SIMULATION'}
                </p>
              </div>
            )}
            {isRunning && (
              <div className="ds-card rounded-ds-xl p-5 flex items-center justify-center gap-3">
                <Loader2 className="w-4 h-4 text-ds-accent animate-spin" />
                <span className="text-caption text-ds-text-muted font-mono">
                  {lang === 'ar' ? 'بناء النموذج الزمني...' : 'Building temporal model...'}
                </span>
              </div>
            )}
            {hasResults && (
              <TimelinePanel
                steps={mockSimulationSteps}
                activeStep={currentStep}
                onStepChange={setCurrentStep}
              />
            )}
          </div>
        </div>

        {/* ═══ RIGHT SIDEBAR — Intelligence + Propagation Panels ═══ */}
        <div className="w-[360px] bg-ds-surface border-l border-ds-border overflow-y-auto flex flex-col" style={{ borderLeft: lang === 'ar' ? 'none' : undefined, borderRight: lang === 'ar' ? '1px solid var(--ds-border)' : undefined }}>
          <div className="p-4 space-y-4 flex flex-col h-full">

            {/* Action buttons */}
            {hasResults && (
              <div className="flex gap-2 flex-shrink-0">
                <button onClick={handleRunSimulation} className="flex-1 ds-btn-primary text-micro">
                  <Play className="w-3.5 h-3.5" />
                  {lang === 'ar' ? 'إعادة' : 'Rerun'}
                </button>
                <button onClick={handleReset} className="flex-1 ds-btn-secondary text-micro">
                  <RotateCcw className="w-3.5 h-3.5" />
                  {lang === 'ar' ? 'إعادة تعيين' : 'Reset'}
                </button>
              </div>
            )}

            {/* Propagation Results — REAL engine output */}
            {hasResults && propagationResult && (
              <>
                <ExplanationPanel
                  explanation={propagationResult.explanation}
                  confidence={propagationResult.confidence}
                  totalLoss={propagationResult.totalLoss}
                  spreadLevel={propagationResult.spreadLevel}
                />
                <ImpactChainPanel chain={propagationResult.propagationChain} />
                <TopDriversPanel drivers={propagationResult.topDrivers} />
                <SectorImpactPanel sectors={propagationResult.affectedSectors} />
              </>
            )}

            {/* Report */}
            {!hasResults && (
              <ReportPanel report={null} />
            )}

            {/* Analyst / Chat */}
            <div className="flex-1 min-h-0 flex flex-col">
              <ChatPanel
                initialMessages={
                  hasResults
                    ? mockChatMessages
                    : [
                        {
                          id: '1',
                          role: 'assistant' as const,
                          content: lang === 'ar'
                            ? 'قم بتشغيل المحاكاة لتفعيل واجهة المحلل.'
                            : 'Run a simulation to activate the analyst interface.',
                        },
                      ]
                }
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
