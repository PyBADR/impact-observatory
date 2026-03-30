import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function getSpreadColor(level: string): string {
  switch (level) {
    case 'high': return 'text-ds-danger'
    case 'medium': return 'text-ds-warning'
    case 'low': return 'text-ds-success'
    default: return 'text-ds-text-secondary'
  }
}

export function getSpreadBg(level: string): string {
  switch (level) {
    case 'high': return 'bg-ds-danger-dim text-ds-danger'
    case 'medium': return 'bg-ds-warning-dim text-ds-warning'
    case 'low': return 'bg-ds-success-dim text-ds-success'
    default: return 'bg-ds-card text-ds-text-secondary'
  }
}

export function getNodeColor(type: string): string {
  const colors: Record<string, string> = {
    // Core entity types
    Topic: '#5B7BF8',
    Region: '#2DD4A0',
    Organization: '#F5A623',
    Person: '#EF5454',
    Platform: '#A78BFA',
    Event: '#F97316',
    // Lowercase variants (from flat mock-data)
    topic: '#5B7BF8',
    region: '#2DD4A0',
    organization: '#F5A623',
    person: '#EF5454',
    platform: '#A78BFA',
    event: '#F97316',
    media: '#A78BFA',
    // GCC layer names (when used as node type)
    geography: '#2DD4A0',
    infrastructure: '#F5A623',
    economy: '#5B7BF8',
    finance: '#A78BFA',
    society: '#EF5454',
  }
  return colors[type] || '#5B7BF8'
}

/** Map GCC layer to color */
export function getLayerColor(layer: string): string {
  const colors: Record<string, string> = {
    geography: '#2DD4A0',
    infrastructure: '#F5A623',
    economy: '#5B7BF8',
    finance: '#A78BFA',
    society: '#EF5454',
  }
  return colors[layer] || '#5B7BF8'
}

export function getNodeGlowIntensity(weight: number): number {
  return Math.max(10, Math.round(weight * 50))
}
