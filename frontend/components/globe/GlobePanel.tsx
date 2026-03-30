'use client'

import { useEffect, useRef, useState, useMemo } from 'react'
import { Globe as GlobeIcon, Maximize, ZoomIn, ZoomOut } from 'lucide-react'
import { nodeCoordinates, shippingRoutes, aviationRoutes } from '@/lib/gcc-coordinates'
import type { GCCNode, GCCEdge, GCCLayer } from '@/lib/gcc-graph'
import { getLayerColor } from '@/lib/utils'

/* ═══════════════════════════════════════════════════
   Deevo Sim — Globe Panel (Canvas-based)
   Mathematical Mode: node glow = normalized impact
   ═══════════════════════════════════════════════════ */

interface GlobePanelProps {
  nodes: GCCNode[]
  edges: GCCEdge[]
  nodeImpacts: Map<string, number>
  systemEnergy: number
  onNodeClick?: (nodeId: string) => void
}

/* Mercator projection for GCC region */
function projectToCanvas(
  lat: number, lng: number,
  canvasW: number, canvasH: number,
  center: { lat: number; lng: number },
  zoom: number
): { x: number; y: number } {
  const scale = canvasW * zoom / 20
  const x = canvasW / 2 + (lng - center.lng) * scale
  const y = canvasH / 2 - (lat - center.lat) * scale
  return { x, y }
}

export default function GlobePanel({ nodes, edges, nodeImpacts, systemEnergy, onNodeClick }: GlobePanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animRef = useRef<number>(0)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1.0)
  const [center] = useState({ lat: 25.5, lng: 52.0 })
  const [canvasSize, setCanvasSize] = useState({ w: 800, h: 500 })

  // Compute normalized impacts
  const normalizedImpacts = useMemo(() => {
    const map = new Map<string, number>()
    const energy = systemEnergy || 1
    for (const [id, impact] of nodeImpacts) {
      map.set(id, Math.abs(impact) / energy)
    }
    return map
  }, [nodeImpacts, systemEnergy])

  // Resize observer
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const parent = canvas.parentElement
    if (!parent) return
    const obs = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setCanvasSize({ w: Math.floor(width), h: Math.floor(height) })
    })
    obs.observe(parent)
    return () => obs.disconnect()
  }, [])

  // Main render loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = canvasSize.w * 2
    canvas.height = canvasSize.h * 2
    ctx.scale(2, 2)

    let frame = 0

    const draw = () => {
      frame++
      const w = canvasSize.w
      const h = canvasSize.h
      ctx.clearRect(0, 0, w, h)

      // Background
      ctx.fillStyle = '#080810'
      ctx.fillRect(0, 0, w, h)

      // Grid
      ctx.strokeStyle = '#12121F'
      ctx.lineWidth = 0.5
      const gridStep = 30 * zoom
      for (let x = 0; x < w; x += gridStep) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke()
      }
      for (let y = 0; y < h; y += gridStep) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke()
      }

      // Draw GCC region outline (simplified)
      drawGCCOutline(ctx, w, h, center, zoom)

      // Draw shipping & aviation routes
      const routeAlpha = 0.15 + Math.sin(frame * 0.02) * 0.05
      drawRoutes(ctx, shippingRoutes, w, h, center, zoom, '#2DD4A088', routeAlpha)
      drawRoutes(ctx, aviationRoutes, w, h, center, zoom, '#5B7BF888', routeAlpha)

      // Draw edges (propagation paths)
      for (const edge of edges) {
        const srcCoord = nodeCoordinates[edge.source]
        const tgtCoord = nodeCoordinates[edge.target]
        if (!srcCoord || !tgtCoord) continue

        const srcPos = projectToCanvas(srcCoord.lat, srcCoord.lng, w, h, center, zoom)
        const tgtPos = projectToCanvas(tgtCoord.lat, tgtCoord.lng, w, h, center, zoom)

        const srcImpact = Math.abs(nodeImpacts.get(edge.source) ?? 0)
        const propagationStrength = Math.abs(edge.weight * srcImpact)
        const alpha = Math.max(0.05, Math.min(0.6, propagationStrength))

        // Edge line
        ctx.beginPath()
        ctx.moveTo(srcPos.x, srcPos.y)
        ctx.lineTo(tgtPos.x, tgtPos.y)
        ctx.strokeStyle = `rgba(91, 123, 248, ${alpha})`
        ctx.lineWidth = 0.5 + propagationStrength * 2
        ctx.stroke()

        // Animated flow dot
        if (propagationStrength > 0.05) {
          const flowSpeed = Math.max(0.005, propagationStrength * 0.02)
          const t = (frame * flowSpeed) % 1
          const fx = srcPos.x + (tgtPos.x - srcPos.x) * t
          const fy = srcPos.y + (tgtPos.y - srcPos.y) * t
          ctx.beginPath()
          ctx.arc(fx, fy, 1.5 + propagationStrength * 2, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(91, 123, 248, ${alpha * 1.5})`
          ctx.fill()
        }
      }

      // Draw nodes
      for (const node of nodes) {
        const coord = nodeCoordinates[node.id]
        if (!coord) continue
        const pos = projectToCanvas(coord.lat, coord.lng, w, h, center, zoom)
        const impact = Math.abs(nodeImpacts.get(node.id) ?? 0)
        const normalizedImpact = normalizedImpacts.get(node.id) ?? 0
        const color = getLayerColor(node.layer)
        const isHovered = hoveredNode === node.id

        // Glow (normalized impact)
        const glowRadius = 8 + normalizedImpact * 40 + (isHovered ? 15 : 0)
        const gradient = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, glowRadius)
        gradient.addColorStop(0, `${color}${isHovered ? '60' : '30'}`)
        gradient.addColorStop(1, `${color}00`)
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, glowRadius, 0, Math.PI * 2)
        ctx.fillStyle = gradient
        ctx.fill()

        // Node circle
        const nodeRadius = 3 + impact * 8 + (isHovered ? 2 : 0)
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, nodeRadius, 0, Math.PI * 2)
        ctx.fillStyle = `${color}${impact > 0.3 ? 'CC' : '88'}`
        ctx.fill()
        ctx.strokeStyle = `${color}${isHovered ? 'FF' : '66'}`
        ctx.lineWidth = isHovered ? 1.5 : 0.8
        ctx.stroke()

        // Inner dot
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, 1.5, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()

        // Pulse ring for high-impact nodes
        if (impact > 0.4) {
          const pulseR = nodeRadius + 3 + Math.sin(frame * 0.05) * 3
          ctx.beginPath()
          ctx.arc(pos.x, pos.y, pulseR, 0, Math.PI * 2)
          ctx.strokeStyle = `${color}25`
          ctx.lineWidth = 1
          ctx.stroke()
        }

        // Label
        ctx.font = `${isHovered ? '600' : '400'} ${isHovered ? 10 : 8}px system-ui, sans-serif`
        ctx.textAlign = 'center'
        ctx.fillStyle = isHovered ? '#E0E0F0' : '#8888A0'
        ctx.fillText(
          node.label.length > 16 ? node.label.slice(0, 14) + '…' : node.label,
          pos.x, pos.y + nodeRadius + 12
        )

        // Impact badge on hover
        if (isHovered && impact > 0) {
          const badge = `Impact: ${(impact * 100).toFixed(0)}%`
          ctx.font = '600 9px "JetBrains Mono", monospace'
          const tw = ctx.measureText(badge).width
          ctx.fillStyle = '#0E0E14E8'
          ctx.beginPath()
          ctx.roundRect(pos.x - tw / 2 - 6, pos.y - nodeRadius - 22, tw + 12, 16, 4)
          ctx.fill()
          ctx.fillStyle = color
          ctx.textAlign = 'center'
          ctx.fillText(badge, pos.x, pos.y - nodeRadius - 10)
        }
      }

      // Legend
      drawLegend(ctx, w, h)

      animRef.current = requestAnimationFrame(draw)
    }

    draw()
    return () => cancelAnimationFrame(animRef.current)
  }, [nodes, edges, nodeImpacts, normalizedImpacts, canvasSize, zoom, center, hoveredNode])

  // Mouse interaction
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const mx = e.clientX - rect.left
    const my = e.clientY - rect.top

    let closest: string | null = null
    let closestDist = 20 // max hover distance in px

    for (const node of nodes) {
      const coord = nodeCoordinates[node.id]
      if (!coord) continue
      const pos = projectToCanvas(coord.lat, coord.lng, canvasSize.w, canvasSize.h, center, zoom)
      const d = Math.hypot(pos.x - mx, pos.y - my)
      if (d < closestDist) {
        closestDist = d
        closest = node.id
      }
    }
    setHoveredNode(closest)
  }

  const handleClick = () => {
    if (hoveredNode && onNodeClick) {
      onNodeClick(hoveredNode)
    }
  }

  return (
    <div className="w-full h-full bg-ds-surface rounded-ds-xl border border-ds-border overflow-hidden relative">
      {/* Header */}
      <div className="ds-panel-header">
        <div className="ds-panel-header-title">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <GlobeIcon size={13} className="text-ds-text-muted" />
          <span className="text-caption font-semibold text-ds-text tracking-tight">Globe View</span>
          <span className="text-nano text-ds-text-dim font-mono ml-1">MATHEMATICAL MODE</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="ds-panel-header-meta">{nodes.length} nodes · GCC Region</span>
          <button onClick={() => setZoom(z => Math.min(z * 1.3, 3))} className="p-1 rounded hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-text"><ZoomIn size={13} /></button>
          <button onClick={() => setZoom(z => Math.max(z / 1.3, 0.3))} className="p-1 rounded hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-text"><ZoomOut size={13} /></button>
          <button onClick={() => setZoom(1)} className="p-1 rounded hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-text"><Maximize size={13} /></button>
        </div>
      </div>

      {/* Canvas */}
      <div className="h-[calc(100%-52px)]">
        <canvas
          ref={canvasRef}
          className="w-full h-full"
          style={{ cursor: hoveredNode ? 'pointer' : 'crosshair' }}
          onMouseMove={handleMouseMove}
          onClick={handleClick}
        />
      </div>
    </div>
  )
}

/* — Helper: Draw GCC outline — */
function drawGCCOutline(ctx: CanvasRenderingContext2D, w: number, h: number, center: { lat: number; lng: number }, zoom: number) {
  // Simplified Arabian Peninsula outline
  const coastline: [number, number][] = [
    [30.0, 47.5], [29.5, 48.0], [28.8, 48.5], [28.5, 49.0],
    [27.5, 49.5], [26.5, 50.0], [26.0, 50.2], [25.5, 50.5],
    [25.0, 51.0], [24.5, 51.5], [24.0, 52.0], [23.5, 53.0],
    [23.0, 55.0], [22.5, 56.0], [22.5, 57.0], [23.0, 58.0],
    [23.5, 59.0], [24.0, 59.5], [25.0, 58.0], [25.5, 57.0],
    [26.0, 56.5], [26.5, 56.4], [26.5, 55.5], [25.5, 55.5],
    [25.0, 55.2], [24.5, 54.5], [24.0, 53.5], [24.2, 54.0],
    [24.5, 54.5], [25.0, 55.0], [25.5, 55.2], [26.0, 55.5],
    [26.5, 56.0], [27.0, 56.5], [28.0, 56.0], [29.0, 52.0],
    [29.5, 49.5], [30.0, 48.0], [30.0, 47.5],
  ]

  ctx.beginPath()
  coastline.forEach(([lat, lng], i) => {
    const { x, y } = projectToCanvas(lat, lng, w, h, center, zoom)
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.closePath()
  ctx.fillStyle = '#0D0D1A'
  ctx.fill()
  ctx.strokeStyle = '#1A1A30'
  ctx.lineWidth = 1
  ctx.stroke()
}

/* — Helper: Draw routes — */
function drawRoutes(
  ctx: CanvasRenderingContext2D,
  routes: { from: { lat: number; lng: number }; to: { lat: number; lng: number } }[],
  w: number, h: number,
  center: { lat: number; lng: number },
  zoom: number,
  color: string,
  alpha: number
) {
  for (const route of routes) {
    const from = projectToCanvas(route.from.lat, route.from.lng, w, h, center, zoom)
    const to = projectToCanvas(route.to.lat, route.to.lng, w, h, center, zoom)
    ctx.beginPath()
    ctx.moveTo(from.x, from.y)
    // Curved path
    const mx = (from.x + to.x) / 2
    const my = (from.y + to.y) / 2 - 15
    ctx.quadraticCurveTo(mx, my, to.x, to.y)
    ctx.strokeStyle = color
    ctx.lineWidth = 0.8
    ctx.setLineDash([4, 4])
    ctx.globalAlpha = alpha
    ctx.stroke()
    ctx.setLineDash([])
    ctx.globalAlpha = 1
  }
}

/* — Helper: Draw legend — */
function drawLegend(ctx: CanvasRenderingContext2D, w: number, h: number) {
  const layers: [string, string][] = [
    ['Geography', '#2DD4A0'],
    ['Infrastructure', '#F5A623'],
    ['Economy', '#5B7BF8'],
    ['Finance', '#A78BFA'],
    ['Society', '#EF5454'],
  ]
  const lx = 12
  let ly = h - 12 - layers.length * 16

  ctx.fillStyle = '#0A0A12E0'
  ctx.beginPath()
  ctx.roundRect(lx - 4, ly - 8, 110, layers.length * 16 + 12, 6)
  ctx.fill()

  ctx.font = '500 8px system-ui, sans-serif'
  for (const [label, color] of layers) {
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(lx + 4, ly + 2, 3, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = '#8888A0'
    ctx.textAlign = 'left'
    ctx.fillText(label, lx + 14, ly + 5)
    ly += 16
  }
}
