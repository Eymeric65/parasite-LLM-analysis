import { getDistance } from 'geolib'
import type { Document, Finding } from '../data/types'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface SpeciesStats {
  name: string
  count: number         // total findings (including those without coords)
  maxDistanceKm: number // max great-circle distance between any two geolocated findings
}

export interface DocumentStats {
  document: Document
  count: number
  maxDistanceKm: number
}

export type SortKey = 'alpha' | 'count' | 'distance'

// ─── Distance Helpers ─────────────────────────────────────────────────────────

interface GeoPoint { latitude: number; longitude: number }

/**
 * Given a list of findings, extract all points that have valid coordinates,
 * then return the maximum great-circle distance (in km) between any two of
 * them.  Returns 0 when fewer than two geolocated findings exist.
 */
function maxPairwiseDistanceKm(findings: Finding[]): number {
  const points: GeoPoint[] = findings
    .filter((f): f is Finding & { latitude: number; longitude: number } =>
      f.latitude !== null && f.longitude !== null,
    )
    .map((f) => ({ latitude: f.latitude, longitude: f.longitude }))

  let maxM = 0
  for (let i = 0; i < points.length; i++) {
    for (let j = i + 1; j < points.length; j++) {
      const d = getDistance(points[i]!, points[j]!)
      if (d > maxM) maxM = d
    }
  }
  return maxM / 1000 // convert metres → km
}

// ─── Species Stats ────────────────────────────────────────────────────────────

/**
 * Build stats for every unique species (case-insensitive) for the given role
 * ('parasite' | 'host').  The first-encountered capitalisation is kept as the
 * canonical display name.
 */
export function buildSpeciesStats(
  findings: Finding[],
  role: 'parasite' | 'host',
): SpeciesStats[] {
  const key = role === 'parasite' ? 'parasite_species' : 'host_species'

  // Group findings by species (case-insensitive)
  const groups = new Map<string, { canonical: string; findings: Finding[] }>()
  for (const f of findings) {
    const raw = f[key]
    const lc  = raw.toLowerCase()
    if (!groups.has(lc)) {
      groups.set(lc, { canonical: raw, findings: [] })
    }
    groups.get(lc)!.findings.push(f)
  }

  return [...groups.values()].map(({ canonical, findings: fs }) => ({
    name:          canonical,
    count:         fs.length,
    maxDistanceKm: maxPairwiseDistanceKm(fs),
  }))
}

// ─── Document Stats ───────────────────────────────────────────────────────────

export function buildDocumentStats(
  findings: Finding[],
  documents: Document[],
): DocumentStats[] {
  const findingsByDoc = new Map<number, Finding[]>()
  for (const f of findings) {
    const arr = findingsByDoc.get(f.document_id) ?? []
    arr.push(f)
    findingsByDoc.set(f.document_id, arr)
  }

  return documents.map((doc) => {
    const fs = findingsByDoc.get(doc.id) ?? []
    return {
      document:      doc,
      count:         fs.length,
      maxDistanceKm: maxPairwiseDistanceKm(fs),
    }
  })
}

// ─── Sorting ──────────────────────────────────────────────────────────────────

export function sortSpeciesStats(stats: SpeciesStats[], key: SortKey): SpeciesStats[] {
  const copy = [...stats]
  switch (key) {
    case 'count':
      return copy.sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
    case 'distance':
      return copy.sort((a, b) => b.maxDistanceKm - a.maxDistanceKm || a.name.localeCompare(b.name))
    default: // 'alpha'
      return copy.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()))
  }
}

export function sortDocumentStats(stats: DocumentStats[], key: SortKey): DocumentStats[] {
  const copy = [...stats]
  switch (key) {
    case 'count':
      return copy.sort((a, b) => b.count - a.count || a.document.id - b.document.id)
    case 'distance':
      return copy.sort(
        (a, b) => b.maxDistanceKm - a.maxDistanceKm || a.document.id - b.document.id,
      )
    default:
      return copy.sort((a, b) => a.document.id - b.document.id)
  }
}

// ─── Formatting Helpers ───────────────────────────────────────────────────────

export function formatDistance(km: number): string {
  if (km === 0)     return '—'
  if (km < 1)      return `${Math.round(km * 1000)} m`
  if (km < 1000)   return `${Math.round(km)} km`
  return `${(km / 1000).toFixed(1)}k km`
}
