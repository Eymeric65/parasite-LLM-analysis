import L from 'leaflet'
import type { Finding } from '../data/types'

// ─── Configuration ────────────────────────────────────────────────────────────

/** Grid cell size in degrees for clustering nearly-identical locations. */
const CLUSTER_PRECISION = 3

/**
 * Base ring radius in pixels at the reference zoom.
 * Scales linearly with zoom so it shrinks at world-level and grows when close.
 */
const BASE_RING_PX   = 18
const REFERENCE_ZOOM = 8
const MIN_RING_PX    = 8
const MAX_RING_PX    = 28

/** Max markers per ring before opening a new one. */
const RING_CAPACITY = 6

/** Organic jitter as a fraction of the ring radius. */
const JITTER_FRACTION = 0.35

// ─── Public Types ─────────────────────────────────────────────────────────────

export interface ClusterMember {
  finding: Finding
  spreadLat: number
  spreadLng: number
}

export interface ClusterDef {
  key: string
  centerLat: number
  centerLng: number
  /** Always ≥ 1.  Single-member clusters need no spiderfy. */
  members: ClusterMember[]
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function gridKey(lat: number, lng: number): string {
  return `${lat.toFixed(CLUSTER_PRECISION)},${lng.toFixed(CLUSTER_PRECISION)}`
}

/**
 * Deterministic pseudo-random generator seeded by a string.
 * Produces stable jitter that doesn't change across redraws.
 */
function seededRandom(seed: string): () => number {
  let h = 2166136261 >>> 0
  for (let i = 0; i < seed.length; i++) {
    h = Math.imul(h ^ seed.charCodeAt(i), 16777619) >>> 0
  }
  return () => {
    h = Math.imul(h ^ (h >>> 16), 2246822507) >>> 0
    h = Math.imul(h ^ (h >>> 13), 3266489909) >>> 0
    h = ((h ^ (h >>> 16)) >>> 0) / 4294967296
    return h
  }
}

function ringRadiusPx(zoom: number): number {
  const scaled = BASE_RING_PX * (zoom / REFERENCE_ZOOM)
  return Math.max(MIN_RING_PX, Math.min(MAX_RING_PX, scaled))
}

/**
 * Compute one shared rotation angle for an entire cluster from its key.
 * All members use this same rotation so the ring stays coherent.
 */
function clusterRotation(clusterKey: string): number {
  return seededRandom(clusterKey)() * Math.PI * 2
}

function organicOffset(
  index: number,
  total: number,
  zoom: number,
  clusterRot: number,  // shared for all members of the same cluster
  jitterSeed: string,  // per-member seed for small individual jitter only
): [number, number] {
  if (total === 1) return [0, 0]

  const rng = seededRandom(jitterSeed)

  let ring = 0
  let remaining = index
  while (remaining >= RING_CAPACITY) {
    remaining -= RING_CAPACITY
    ring++
  }
  const ringCount  = Math.min(RING_CAPACITY, total - ring * RING_CAPACITY)
  const ringRadius = ringRadiusPx(zoom) * (ring + 1)

  // Even base spacing + shared cluster rotation + small per-member angle jitter
  const baseAngle   = (2 * Math.PI * remaining) / ringCount
  const angleJitter = (rng() - 0.5) * (Math.PI / ringCount) * 0.6
  const angle       = baseAngle + clusterRot + angleJitter

  const radialJitter = (rng() - 0.5) * 2 * JITTER_FRACTION * ringRadius
  const r            = ringRadius + radialJitter

  return [Math.cos(angle) * r, Math.sin(angle) * r]
}

// ─── Main Export ──────────────────────────────────────────────────────────────

/**
 * Groups findings by geographic cluster and computes per-member spread
 * positions in pixel space (then back to lat/lng) at the current zoom.
 *
 * Returned ClusterDefs are the source of truth for the spiderfy animation
 * in MapView: markers start at `centerLat/Lng` and animate to
 * `member.spreadLat/Lng` on hover.
 */
export function buildClusters(findings: Finding[], map: L.Map): ClusterDef[] {
  const zoom = map.getZoom()

  // Group by grid cell
  const groups = new Map<string, Array<{ finding: Finding; lat: number; lng: number }>>()
  for (const f of findings) {
    if (f.latitude === null || f.longitude === null) continue
    const key = gridKey(f.latitude, f.longitude)
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push({ finding: f, lat: f.latitude, lng: f.longitude })
  }

  const clusters: ClusterDef[] = []

  for (const [key, members] of groups.entries()) {
    const centerLat = members.reduce((s, m) => s + m.lat, 0) / members.length
    const centerLng = members.reduce((s, m) => s + m.lng, 0) / members.length
    const centerPx  = map.latLngToContainerPoint(L.latLng(centerLat, centerLng))

    // One shared rotation for the whole cluster so the ring looks coherent
    const clusterRot = clusterRotation(key)

    const clusterMembers: ClusterMember[] = members.map(({ finding }, i) => {
      if (members.length === 1) {
        return { finding, spreadLat: centerLat, spreadLng: centerLng }
      }
      const seed         = `${finding.parasite_species}|${finding.host_species}|${i}`
      const [dx, dy]     = organicOffset(i, members.length, zoom, clusterRot, seed)
      const { lat, lng } = map.containerPointToLatLng(L.point(centerPx.x + dx, centerPx.y + dy))
      return { finding, spreadLat: lat, spreadLng: lng }
    })

    clusters.push({ key, centerLat, centerLng, members: clusterMembers })
  }

  return clusters
}

