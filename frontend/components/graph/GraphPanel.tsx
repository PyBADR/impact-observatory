'use client'
import { useState, useRef, useEffect, useCallback } from 'react'
import { Eye, EyeOff, ZoomIn, ZoomOut, Maximize } from 'lucide-react'
import { getNodeColor } from '@/lib/utils'

/* ══════════════════════════════════════════════════
   Deevo Sim — Pure SVG Graph Panel
   No React Flow dependency — zero crash risk
   ══════════════════════════════════════════════════ */

/* Accept ANY node shape — flat or nested */
interface NodeData {
  id: string
  position?: { x: number; y: number }
  data?: { label: string; type: string; weight: number }
  label?: string
  type?: string
  weight?: number
}

interface EdgeData {
  id: string
  source: string
  target: string
  label?: string
  animated?: boolean
}

/* Internal normalized node used for rendering */
interface NormalizedNode {
  id: string
  x: number
  y: number
  label: string
  type: string
  weight: number
}

interface GraphPanelProps {
  initialNodes: NodeData[]
  initialEdges: EdgeData[]
}

/* ──────────────────────────────────────────────
   Animated Edge — SVG path with flow animation
   ────────────────────────────────────────────── */
function AnimatedEdge({
  x1, y1, x2, y2, label, animated, focusMode,
}: {
  x1: number; y1: number; x2: number; y2: number
  label?: string; animated?: boolean; focusMode: boolean
}) {
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2
  const id = `edge-${x1}-${y1}-${x2}-${y2}`

  return (
    <g>
      <line
        x1={x1} y1={y1} x2={x2} y2={y2}
        stroke={focusMode ? '#2A2A3D' : '#1E1E30'}
        strokeWidth={1.2}
        strokeDasharray={animated ? '6 4' : undefined}
        className={animated ? 'animate-dash' : ''}
      />
      {/* Glow line */}
      <line
        x1={x1} y1={y1} x2={x2} y2={y2}
        stroke={focusMode ? '#2A2A3D' : '#1E1E30'}
        strokeWidth={3}
        strokeOpacity={0.15}
        filter="url(#edgeGlow)"
      />
      {label && (
        <>
          <rect
            x={mx - label.length * 3.2 - 6}
            y={my - 8}
            width={label.length * 6.4 + 12}
            height={16}
            rx={4}
            fill="#0E0E14"
            fillOpacity={0.92}
            stroke="#1A1A2A"
            strokeWidth={0.5}
          />
          <text
            x={mx} y={my + 3}
            textAnchor="middle"
            fill="#5A5A70"
            fontSize={8}
            fontFamily="'JetBrains Mono', monospace"
          >
            {label}
          </text>
        </>
      )}
    </g>
  )
}

/* ──────────────────────────────────────────────
   Graph Node — cinematic glowing circle
   ────────────────────────────────────────────── */
function GraphNode({
  x, y, label, type, weight, onHover, isHovered,
}: {
  x: number; y: number; label: string; type: string; weight: number
  onHover: (id: string | null) => void; isHovered: boolean
}) {
  const color = getNodeColor(type)
  const r = 18 + weight * 18
  const glowR = r * 2.2
  const innerR = 3

  return (
    <g
      onMouseEnter={() => onHover(label)}
      onMouseLeave={() => onHover(null)}
      style={{ cursor: 'pointer' }}
    >
      {/* Outer glow */}
      <circle
        cx={x} cy={y} r={glowR}
        fill={`url(#glow-${type})`}
        opacity={isHovered ? 0.5 : 0.2}
        className="transition-opacity duration-300"
      />

      {/* Node ring */}
      <circle
        cx={x} cy={y} r={r}
        fill={`${color}12`}
        stroke={`${color}${isHovered ? '88' : '44'}`}
        strokeWidth={isHovered ? 1.5 : 1}
        className="transition-all duration-300"
        filter="url(#nodeGlow)"
      />

      {/* Inner dot */}
      <circle
        cx={x} cy={y - (r > 28 ? 6 : 4)}
        r={innerR}
        fill={color}
        filter="url(#dotGlow)"
      />

      {/* Label */}
      <text
        x={x} y={y + (r > 28 ? 2 : 1)}
        textAnchor="middle"
        fill="#E0E0F0"
        fontSize={r > 28 ? 9 : 8}
        fontWeight={600}
        fontFamily="system-ui, sans-serif"
      >
        {label.length > 14 ? label.slice(0, 12) + '…' : label}
      </text>

      {/* Hover tooltip */}
      {isHovered && (
        <g>
          <rect
            x={x - 40} y={y + r + 6}
            width={80} height={18}
            rx={4}
            fill="#0E0E14"
            fillOpacity={0.95}
            stroke={`${color}30`}
            strokeWidth={0.5}
          />
          <text
            x={x} y={y + r + 18}
            textAnchor="middle"
            fill="#8888A0"
            fontSize={8}
            fontFamily="'JetBrains Mono', monospace"
          >
            {type} · {Math.round(weight * 100)}%
          </text>
        </g>
      )}

      {/* Pulse ring for high-weight nodes */}
      {weight > 0.7 && (
        <circle
          cx={x} cy={y} r={r + 4}
          fill="none"
          stroke={`${color}30`}
          strokeWidth={1}
          className="animate-ping-slow"
        />
      )}
    </g>
  )
}

/* ──────────────────────────────────────────────
   Graph Panel — main export
   ────────────────────────────────────────────── */
export default function GraphPanel({ initialNodes, initialEdges }: GraphPanelProps) {
  const [focusMode, setFocusMode] = useState(false)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })
  const svgRef = useRef<SVGSVGElement>(null)

  /* ── Normalize nodes: handle BOTH flat and nested formats ── */
  const nodes: NormalizedNode[] = initialNodes.map((n, i) => {
    // Extract label/type/weight from whichever shape we received
    const label = n.data?.label || n.label || 'Unknown'
    const type  = n.data?.type  || (n.type !== 'custom' ? n.type : undefined) || 'Topic'
    const weight = n.data?.weight ?? n.weight ?? 0.5

    // Auto-layout in ellipse if no explicit position
    const hasPosition = n.position && (n.position.x !== 0 || n.position.y !== 0)
    const angle = (2 * Math.PI * i) / initialNodes.length - Math.PI / 2
    const cx = 425 + 220 * Math.cos(angle)
    const cy = 275 + 170 * Math.sin(angle)
    const x = hasPosition ? n.position!.x + 40 : cx
    const y = hasPosition ? n.position!.y + 40 : cy

    return { id: n.id, x, y, label, type, weight }
  })

  // Node center lookup for edge rendering
  const nodeMap = new Map(nodes.map(n => [n.id, n]))

  const getNodeCenter = (nodeId: string) => {
    const node = nodeMap.get(nodeId)
    if (!node) return { x: 425, y: 275 }
    return { x: node.x, y: node.y }
  }

  // Zoom controls
  const handleZoomIn = () => setZoom(z => Math.min(z * 1.3, 3))
  const handleZoomOut = () => setZoom(z => Math.max(z / 1.3, 0.3))
  const handleFitView = () => { setZoom(1); setPan({ x: 0, y: 0 }) }

  // Pan handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsPanning(true)
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }, [pan])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isPanning) {
      setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y })
    }
  }, [isPanning, panStart])

  const handleMouseUp = useCallback(() => setIsPanning(false), [])

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setZoom(z => Math.max(0.3, Math.min(3, z * delta)))
  }, [])

  // Unique types for gradient defs
  const uniqueTypes = [...new Set(nodes.map(n => n.type))]

  return (
    <div className="w-full h-full bg-ds-surface rounded-ds-xl border border-ds-border overflow-hidden relative">
      {/* Panel header */}
      <div className="ds-panel-header">
        <div className="ds-panel-header-title">
          <div className="w-2 h-2 rounded-full bg-ds-success animate-pulse" />
          <span className="text-caption font-semibold text-ds-text tracking-tight">Entity Graph</span>
          <span className="text-nano text-ds-text-dim font-mono ml-1">LIVE</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="ds-panel-header-meta">{nodes.length} nodes · {initialEdges.length} edges</span>
          <button
            onClick={handleZoomIn}
            className="p-1 rounded hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-text"
            title="Zoom In"
          >
            <ZoomIn size={13} />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 rounded hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-text"
            title="Zoom Out"
          >
            <ZoomOut size={13} />
          </button>
          <button
            onClick={handleFitView}
            className="p-1 rounded hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-text"
            title="Fit View"
          >
            <Maximize size={13} />
          </button>
          <button
            onClick={() => setFocusMode(!focusMode)}
            className="p-1.5 rounded-md hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-text"
            title={focusMode ? 'Exit Focus Mode' : 'Focus Mode'}
          >
            {focusMode ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>
      </div>

      {/* SVG Graph */}
      <div
        className="h-[calc(100%-52px)] overflow-hidden"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        style={{ cursor: isPanning ? 'grabbing' : 'grab' }}
      >
        <svg
          ref={svgRef}
          viewBox="0 0 850 550"
          className="w-full h-full"
          style={{
            transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
            transformOrigin: 'center center',
          }}
        >
          {/* Defs — gradients, filters, animations */}
          <defs>
            {uniqueTypes.map(type => {
              const color = getNodeColor(type)
              return (
                <radialGradient key={type} id={`glow-${type}`}>
                  <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </radialGradient>
              )
            })}
            <filter id="nodeGlow">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="dotGlow">
              <feGaussianBlur stdDeviation="1.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="edgeGlow">
              <feGaussianBlur stdDeviation="2" />
            </filter>
          </defs>

          {/* Grid background */}
          <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse">
            <circle cx="0.5" cy="0.5" r="0.5" fill="#1A1A28" />
          </pattern>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Edges */}
          {initialEdges.map(edge => {
            const source = getNodeCenter(edge.source)
            const target = getNodeCenter(edge.target)
            return (
              <AnimatedEdge
                key={edge.id}
                x1={source.x} y1={source.y}
                x2={target.x} y2={target.y}
                label={edge.label}
                animated={edge.animated}
                focusMode={focusMode}
              />
            )
          })}

          {/* Nodes */}
          {nodes.map(node => (
            <GraphNode
              key={node.id}
              x={node.x}
              y={node.y}
              label={node.label}
              type={node.type}
              weight={node.weight}
              onHover={setHoveredNode}
              isHovered={hoveredNode === node.label}
            />
          ))}
        </svg>
      </div>

      {/* Focus mode overlay */}
      {focusMode && (
        <div className="absolute top-14 left-1/2 -translate-x-1/2 bg-ds-accent/10 border border-ds-accent/20 backdrop-blur-sm rounded-full px-3 py-1 text-nano font-mono text-ds-accent flex items-center gap-1.5">
          <Eye size={10} />
          FOCUS MODE
        </div>
      )}

      {/* CSS animations */}
      <style jsx>{`
        @keyframes dash {
          to { stroke-dashoffset: -20; }
        }
        .animate-dash {
          animation: dash 1.5s linear infinite;
        }
        @keyframes ping-slow {
          0% { opacity: 0.6; transform-origin: center; }
          100% { opacity: 0; transform: scale(1.4); transform-origin: center; }
        }
        .animate-ping-slow {
          animation: ping-slow 2s ease-out infinite;
        }
      `}</style>
    </div>
  )
}
