'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  RotateCcw,
  Settings,
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
} from 'lucide-react'

import GraphPanel from '@/components/graph/GraphPanel'
import TimelinePanel from '@/components/simulation/TimelinePanel'
import ReportPanel from '@/components/report/ReportPanel'
import ChatPanel from '@/components/chat/ChatPanel'
import {
  mockScenarios,
  mockGraphNodes,
  mockGraphEdges,
  mockSimulationSteps,
  mockReport,
  mockChatMessages,
} from '@/lib/mock-data'

const processingSteps = [
  { label: 'Parsing scenario input' },
  { label: 'Extracting entities' },
  { label: 'Building relationship graph' },
  { label: 'Generating agent personas' },
  { label: 'Running simulation engine' },
  { label: 'Compiling intelligence brief' },
]

export default function DemoPage() {
  const [selectedScenario, setSelectedScenario] = useState(mockScenarios[0])
  const [scenarioTitle, setScenarioTitle] = useState(mockScenarios[0].title)
  const [scenarioText, setScenarioText] = useState(mockScenarios[0].scenario)
  const [country, setCountry] = useState(mockScenarios[0].country)
  const [category, setCategory] = useState(mockScenarios[0].category)
  const [isRunning, setIsRunning] = useState(false)
  const [hasResults, setHasResults] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [processingStep, setProcessingStep] = useState(0)
  const [isMobile, setIsMobile] = useState(false)
  const [runId, setRunId] = useState('\u2014')
  const [runTimestamp, setRunTimestamp] = useState('\u2014')

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 1024)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    if (!isRunning) return
    const interval = setInterval(() => {
      setProcessingStep(prev => {
        if (prev < processingSteps.length - 1) return prev + 1
        return prev
      })
    }, 700)
    return () => clearInterval(interval)
  }, [isRunning])

  useEffect(() => {
    if (processingStep === processingSteps.length - 1 && isRunning) {
      const timeout = setTimeout(() => {
        setIsRunning(false)
        setHasResults(true)
        setCurrentStep(0)
      }, 600)
      return () => clearTimeout(timeout)
    }
  }, [processingStep, isRunning])

  const handleScenarioSelect = (scenario: typeof mockScenarios[0]) => {
    setSelectedScenario(scenario)
    setScenarioTitle(scenario.title)
    setScenarioText(scenario.scenario)
    setCountry(scenario.country)
    setCategory(scenario.category)
    setHasResults(false)
    setCurrentStep(0)
  }

  const handleReset = () => {
    setHasResults(false)
    setCurrentStep(0)
    setProcessingStep(0)
    setIsRunning(false)
    setRunId('\u2014')
    setRunTimestamp('\u2014')
  }

  const handleRunSimulation = () => {
    setIsRunning(true)
    setProcessingStep(0)
    setHasResults(false)
    setRunId(`SIM-${Math.random().toString(36).substring(2, 8).toUpperCase()}`)
    setRunTimestamp(new Date().toLocaleTimeString('en-US', { hour12: false }))
  }

  const systemStatus = useMemo(() => {
    if (isRunning) return { label: 'PROCESSING', color: 'bg-ds-accent', pulse: true }
    if (hasResults) return { label: 'COMPLETE', color: 'bg-ds-success', pulse: false }
    return { label: 'READY', color: 'bg-ds-text-dim', pulse: false }
  }, [isRunning, hasResults])

  if (isMobile) {
    return (
      <div className="h-screen w-full bg-ds-bg flex items-center justify-center p-6">
        <div className="ds-card p-10 text-center max-w-md">
          <div className="w-14 h-14 rounded-full bg-ds-surface-raised border border-ds-border flex items-center justify-center mx-auto mb-5">
            <Globe className="w-6 h-6 text-ds-text-muted" />
          </div>
          <h2 className="text-h3 mb-3">Desktop Required</h2>
          <p className="text-caption text-ds-text-muted mb-8 leading-relaxed">
            The Control Room requires a desktop viewport for the full intelligence experience.
          </p>
          <Link href="/" className="ds-btn-primary">
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen w-full bg-ds-bg flex flex-col overflow-hidden">
      <div className="h-11 border-b border-ds-border bg-ds-surface/80 backdrop-blur-xl flex-shrink-0 flex items-center justify-between px-5">
        <div className="flex items-center gap-3 min-w-0">
          <Link href="/" className="flex items-center gap-2 text-ds-text-muted hover:text-ds-text transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
          </Link>
          <div className="w-px h-5 bg-ds-border" />
          <span className="text-micro font-semibold text-ds-text tracking-tight">DEEVO SIM</span>
          <span className="text-micro text-ds-text-dim font-mono">/</span>
          <span className="text-micro text-ds-text-muted font-mono">Control Room</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${systemStatus.color} ${systemStatus.pulse ? 'animate-pulse' : ''}`} />
            <span className="text-nano font-mono uppercase tracking-[0.15em] text-ds-text-secondary">{systemStatus.label}</span>
          </div>
          {runId !== '\u2014' && (
            <>
              <span className="text-nano text-ds-text-dim">\u00b7</span>
              <span className="text-nano font-mono text-ds-text-dim">
                <Clock size={10} className="inline mr-1 -mt-0.5" />
                {runTimestamp}
              </span>
              <span className="text-nano font-mono text-ds-text-dim">{runId}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-micro text-ds-text-muted truncate max-w-[200px] font-mono">{scenarioTitle}</span>
          <button className="p-1.5 hover:bg-ds-card rounded-md transition-colors text-ds-text-dim hover:text-ds-text">
            <Settings className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-[280px] bg-ds-surface border-r border-ds-border overflow-y-auto flex flex-col">
          <div className="p-5 space-y-5 flex flex-col">
            <div>
              <h3 className="text-nano uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-3 flex items-center gap-2">
                <Radio size={10} />
                Scenario Input
              </h3>
              <div className="space-y-3">
                <input type="text" value={scenarioTitle} onChange={(e) => setScenarioTitle(e.target.value)} placeholder="Scenario title" className="ds-input text-micro" />
                <textarea value={scenarioText} onChange={(e) => setScenarioText(e.target.value)} placeholder="Describe the scenario..." dir="auto" className="ds-input min-h-[100px] resize-none text-micro" />
                <select value={country} onChange={(e) => setCountry(e.target.value)} className="ds-select text-micro">
                  <option value="Saudi Arabia">Saudi Arabia</option>
                  <option value="Kuwait">Kuwait</option>
                  <option value="UAE">UAE</option>
                  <option value="Bahrain">Bahrain</option>
                  <option value="Oman">Oman</option>
                  <option value="Qatar">Qatar</option>
                  <option value="GCC">GCC</option>
                </select>
                <select value={category} onChange={(e) => setCategory(e.target.value)} className="ds-select text-micro">
                  <option value="economy">Economy</option>
                  <option value="public sentiment">Public Sentiment</option>
                  <option value="business reaction">Business Reaction</option>
                  <option value="technology">Technology</option>
                  <option value="policy">Policy</option>
                </select>
              </div>
            </div>

            <button onClick={handleRunSimulation} disabled={isRunning} className="w-full ds-btn-primary disabled:opacity-40 disabled:cursor-not-allowed">
              {isRunning ? (<><Loader2 className="w-4 h-4 animate-spin" />Processing...</>) : (<><Zap className="w-4 h-4" />Run Simulation</>)}
            </button>

            <AnimatePresence>
              {isRunning && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.3 }}>
                  <div className="pt-4 border-t border-ds-border space-y-3">
                    <h3 className="text-nano uppercase tracking-[0.15em] text-ds-text-dim font-semibold flex items-center gap-2">
                      <Activity size={10} className="text-ds-accent" />
                      Pipeline
                    </h3>
                    <div className="space-y-2.5">
                      {processingSteps.map((step, idx) => (
                        <motion.div key={idx} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.05 }} className="flex items-center gap-2.5">
                          {idx < processingStep ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-ds-success flex-shrink-0" />
                          ) : idx === processingStep ? (
                            <Loader2 className="w-3.5 h-3.5 text-ds-accent animate-spin flex-shrink-0" />
                          ) : (
                            <Circle className="w-3.5 h-3.5 text-ds-text-dim flex-shrink-0" />
                          )}
                          <span className={`text-[11px] font-mono ${idx < processingStep ? 'text-ds-text-muted line-through' : idx === processingStep ? 'text-ds-accent' : 'text-ds-text-dim'}`}>{step.label}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="ds-divider" />

            <div>
              <h3 className="text-nano uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-3 flex items-center gap-2">
                <Shield size={10} />
                Presets
              </h3>
              <div className="space-y-2">
                {mockScenarios.slice(0, 3).map((scenario) => (
                  <button key={scenario.id} onClick={() => handleScenarioSelect(scenario)} className={`w-full text-left px-3.5 py-3 rounded-ds-lg border transition-all duration-200 ${selectedScenario.id === scenario.id ? 'bg-ds-accent/8 border-ds-accent/25' : 'bg-ds-bg-alt border-ds-border hover:border-ds-border-hover hover:bg-ds-card/40'}`}>
                    <div className="text-micro font-medium text-ds-text truncate">{scenario.title}</div>
                    <div className="flex items-center gap-1.5 mt-1.5 text-[10px] text-ds-text-dim font-mono">
                      <Globe className="w-3 h-3" />
                      {scenario.country}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 bg-ds-bg overflow-y-auto flex flex-col p-4 gap-4">
          <div className="flex-1 min-h-[420px]">
            {!hasResults && !isRunning && (
              <div className="h-full ds-card rounded-ds-xl flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 ds-grid-bg opacity-20" />
                <div className="relative text-center">
                  <div className="w-12 h-12 rounded-full bg-ds-surface-raised border border-ds-border flex items-center justify-center mx-auto mb-3">
                    <Circle className="w-5 h-5 text-ds-text-dim" />
                  </div>
                  <p className="text-caption text-ds-text-dim">Run a simulation to generate the entity graph</p>
                  <p className="text-nano text-ds-text-dim mt-1 font-mono">AWAITING INPUT</p>
                </div>
              </div>
            )}
            {isRunning && (
              <div className="h-full ds-card rounded-ds-xl flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 ds-grid-bg opacity-20" />
                <div className="relative text-center">
                  <Loader2 className="w-10 h-10 mx-auto mb-3 text-ds-accent animate-spin" />
                  <p className="text-caption text-ds-text-muted">Generating entity graph...</p>
                  <p className="text-nano text-ds-accent font-mono mt-1">SIGNAL PROPAGATION ACTIVE</p>
                </div>
              </div>
            )}
            {hasResults && (
              <GraphPanel initialNodes={mockGraphNodes} initialEdges={mockGraphEdges} />
            )}
          </div>

          <div className="flex-shrink-0">
            {!hasResults && !isRunning && (
              <div className="ds-card rounded-ds-xl p-5 text-center">
                <p className="text-caption text-ds-text-dim font-mono">TIMELINE \u00b7 AWAITING SIMULATION</p>
              </div>
            )}
            {isRunning && (
              <div className="ds-card rounded-ds-xl p-5 flex items-center justify-center gap-3">
                <Loader2 className="w-4 h-4 text-ds-accent animate-spin" />
                <span className="text-caption text-ds-text-muted font-mono">Building temporal model...</span>
              </div>
            )}
            {hasResults && (
              <TimelinePanel steps={mockSimulationSteps} activeStep={currentStep} onStepChange={setCurrentStep} />
            )}
          </div>
        </div>

        <div className="w-[360px] bg-ds-surface border-l border-ds-border overflow-y-auto flex flex-col">
          <div className="p-4 space-y-4 flex flex-col h-full">
            {hasResults && (
              <div className="flex gap-2 flex-shrink-0">
                <button onClick={handleRunSimulation} className="flex-1 ds-btn-primary text-micro">
                  <Play className="w-3.5 h-3.5" />
                  Rerun
                </button>
                <button onClick={handleReset} className="flex-1 ds-btn-secondary text-micro">
                  <RotateCcw className="w-3.5 h-3.5" />
                  Reset
                </button>
              </div>
            )}
            <div className="flex-shrink-0">
              {!hasResults && (<ReportPanel report={null} />)}
              {hasResults && (<ReportPanel report={mockReport} />)}
            </div>
            <div className="flex-1 min-h-0 flex flex-col">
              <ChatPanel initialMessages={hasResults ? mockChatMessages : [{ id: '1', role: 'assistant' as const, content: 'Run a simulation to activate the analyst interface.' }]} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
  }
