<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch } from 'vue'
import { ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { speciesColorSolid } from '../utils/color'
import { buildClusters } from '../utils/spread'
import { useSelection } from '../store/useSelection'
import type { Finding } from '../data/types'
import type { ClusterDef } from '../utils/spread'

// ─── Props ────────────────────────────────────────────────────────────────────

const props = defineProps<{ findings: Finding[] }>()

// ─── State ────────────────────────────────────────────────────────────────────

const { state } = useSelection()
const mapContainer = ref<HTMLElement | null>(null)

let map: L.Map | null = null
let markerLayer: L.LayerGroup | null = null

// ─── Live-cluster bookkeeping ─────────────────────────────────────────────────

interface LiveMember {
  finding: Finding
  spreadLat: number
  spreadLng: number
  /** Current animated position (starts at centroid). */
  currentLat: number
  currentLng: number
  parasiteMarker: L.CircleMarker | null
  hostMarker: L.CircleMarker | null
}

interface LiveCluster {
  def: ClusterDef
  members: LiveMember[]
  spiderLines: L.Polyline[]
  isExpanded: boolean
  animFrame: number | null
  collapseTimer: ReturnType<typeof setTimeout> | null
}

/** All clusters currently on the map. */
let liveClusters: LiveCluster[] = []

// ─── Highlight logic ──────────────────────────────────────────────────────────

function isHighlighted(finding: Finding): boolean {
  if (!state.selection) return true
  if (state.selection.type === 'parasite')
    return finding.parasite_species.toLowerCase() === state.selection.species.toLowerCase()
  if (state.selection.type === 'host')
    return finding.host_species.toLowerCase() === state.selection.species.toLowerCase()
  return finding.document_id === state.selection.documentId
}

function parasiteOptions(finding: Finding): L.CircleMarkerOptions {
  const hl = isHighlighted(finding)
  return {
    radius: hl ? 8 : 5,
    fillColor: speciesColorSolid(finding.parasite_species),
    fillOpacity: hl ? 0.9 : 0.15,
    color: hl ? '#fff' : 'transparent',
    weight: hl ? 1.5 : 0,
  }
}

function hostOptions(finding: Finding): L.CircleMarkerOptions {
  const hl = isHighlighted(finding)
  return {
    radius: hl ? 13 : 9,
    fillColor: 'transparent',
    fillOpacity: 0,
    color: speciesColorSolid(finding.host_species),
    weight: hl ? 2.5 : 1.5,
    opacity: hl ? 0.9 : 0.15,
  }
}

function tooltipHtml(finding: Finding): string {
  return `<div class="map-tooltip">
    <em>${finding.parasite_species}</em> on <em>${finding.host_species}</em><br/>
    <span>${finding.area}, ${finding.country}</span>
  </div>`
}

// ─── Spiderfy animation ───────────────────────────────────────────────────────

const EXPAND_MS  = 260
const EASE = (t: number) => 1 - Math.pow(1 - t, 3) // ease-out cubic

function drawSpiderLines(cluster: LiveCluster): void {
  if (!markerLayer) return
  for (const m of cluster.members) {
    const line = L.polyline(
      [[cluster.def.centerLat, cluster.def.centerLng], [m.spreadLat, m.spreadLng]],
      { color: 'rgba(200,220,255,0.35)', weight: 1, dashArray: '4 5', interactive: false },
    )
    line.addTo(markerLayer)
    cluster.spiderLines.push(line)
  }
}

function removeSpiderLines(cluster: LiveCluster): void {
  for (const line of cluster.spiderLines) {
    markerLayer?.removeLayer(line)
  }
  cluster.spiderLines = []
}

function animateCluster(
  cluster: LiveCluster,
  expanding: boolean,
): void {
  if (cluster.animFrame !== null) {
    cancelAnimationFrame(cluster.animFrame)
    cluster.animFrame = null
  }

  const startPositions = cluster.members.map((m) => ({ lat: m.currentLat, lng: m.currentLng }))
  const startTime      = performance.now()

  function frame(now: number): void {
    const raw   = Math.min((now - startTime) / EXPAND_MS, 1)
    const t     = EASE(raw)

    for (let i = 0; i < cluster.members.length; i++) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const m   = cluster.members[i]!
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const sp  = startPositions[i]!
      const tLat = expanding ? m.spreadLat : cluster.def.centerLat
      const tLng = expanding ? m.spreadLng : cluster.def.centerLng
      m.currentLat = sp.lat + (tLat - sp.lat) * t
      m.currentLng = sp.lng + (tLng - sp.lng) * t
      m.parasiteMarker?.setLatLng([m.currentLat, m.currentLng])
      m.hostMarker?.setLatLng([m.currentLat, m.currentLng])
    }

    if (raw < 1) {
      cluster.animFrame = requestAnimationFrame(frame)
    } else {
      cluster.animFrame = null
      if (!expanding) removeSpiderLines(cluster)
    }
  }

  cluster.animFrame = requestAnimationFrame(frame)
}

/** Snap all members immediately to spread positions (no animation). */
function expandClusterInstant(cluster: LiveCluster): void {
  if (cluster.isExpanded) return
  cluster.isExpanded = true
  for (const m of cluster.members) {
    m.currentLat = m.spreadLat
    m.currentLng = m.spreadLng
    m.parasiteMarker?.setLatLng([m.spreadLat, m.spreadLng])
    m.hostMarker?.setLatLng([m.spreadLat, m.spreadLng])
  }
  drawSpiderLines(cluster)
}

function expandCluster(cluster: LiveCluster): void {
  if (cluster.isExpanded) return
  cluster.isExpanded = true
  drawSpiderLines(cluster)
  animateCluster(cluster, true)
}

/** Returns true if any member matches the current selection. */
function clusterHasHighlight(cluster: LiveCluster): boolean {
  if (!state.selection) return false
  return cluster.members.some((m) => isHighlighted(m.finding))
}

function collapseCluster(cluster: LiveCluster): void {
  if (!cluster.isExpanded) return
  // Keep expanded when the selection is pinning this cluster open
  if (clusterHasHighlight(cluster)) return
  cluster.isExpanded = false
  animateCluster(cluster, false)
}

// ─── Marker building ──────────────────────────────────────────────────────────

function cancelAllClusters(): void {
  for (const c of liveClusters) {
    if (c.animFrame !== null) cancelAnimationFrame(c.animFrame)
    if (c.collapseTimer !== null) clearTimeout(c.collapseTimer)
  }
  liveClusters = []
}

function bindHover(marker: L.CircleMarker, cluster: LiveCluster): void {
  // Single-member clusters don't need spiderfy
  if (cluster.members.length <= 1) return

  marker.on('mouseover', () => {
    if (cluster.collapseTimer !== null) {
      clearTimeout(cluster.collapseTimer)
      cluster.collapseTimer = null
    }
    expandCluster(cluster)
  })

  marker.on('mouseout', () => {
    cluster.collapseTimer = setTimeout(() => {
      cluster.collapseTimer = null
      collapseCluster(cluster)
    }, 120)
  })
}

function rebuildMarkers(): void {
  if (!map || !markerLayer) return

  cancelAllClusters()
  markerLayer.clearLayers()

  const mode   = state.displayMode
  const withCoords = props.findings.filter(
    (f) => f.latitude !== null && f.longitude !== null,
  )

  const clusters = buildClusters(withCoords, map)

  for (const def of clusters) {
    const liveMembers: LiveMember[] = def.members.map((cm) => ({
      finding:    cm.finding,
      spreadLat:  cm.spreadLat,
      spreadLng:  cm.spreadLng,
      currentLat: def.centerLat,
      currentLng: def.centerLng,
      parasiteMarker: null,
      hostMarker:     null,
    }))

    const live: LiveCluster = {
      def,
      members:      liveMembers,
      spiderLines:  [],
      isExpanded:   false,
      animFrame:    null,
      collapseTimer: null,
    }

    for (const m of liveMembers) {
      const tt = tooltipHtml(m.finding)

      if (mode === 'parasites' || mode === 'both') {
        const pm = L.circleMarker([def.centerLat, def.centerLng], parasiteOptions(m.finding))
          .bindTooltip(tt, { className: 'custom-tooltip', direction: 'top' })
          .addTo(markerLayer)
        m.parasiteMarker = pm
        bindHover(pm, live)
      }

      if (mode === 'hosts' || mode === 'both') {
        const hm = L.circleMarker([def.centerLat, def.centerLng], hostOptions(m.finding))
          .bindTooltip(tt, { className: 'custom-tooltip', direction: 'top' })
          .addTo(markerLayer)
        m.hostMarker = hm
        bindHover(hm, live)
      }
    }

    liveClusters.push(live)
  }

  // Auto-expand clusters that contain a highlighted finding whenever a
  // selection is active (instant snap, no animation needed on rebuild).
  if (state.selection) {
    for (const c of liveClusters) {
      if (c.members.length > 1 && clusterHasHighlight(c)) {
        expandClusterInstant(c)
      }
    }
  }
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────

onMounted(() => {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value, { center: [20, 0], zoom: 2 })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution:
      '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
  }).addTo(map)

  markerLayer = L.layerGroup().addTo(map)

  map.on('zoomend', rebuildMarkers)

  rebuildMarkers()
})

onBeforeUnmount(() => {
  cancelAllClusters()
  map?.remove()
  map = null
})

// ─── Reactivity ───────────────────────────────────────────────────────────────

watch(
  [() => props.findings, () => state.displayMode, () => state.selection],
  () => rebuildMarkers(),
)
</script>

<template>
  <div class="map-wrapper">
    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<style scoped>
.map-wrapper {
  flex: 1;
  position: relative;
  min-width: 0;
}

.map-container {
  width: 100%;
  height: 100%;
}
</style>

<!-- Global tooltip styles (unscoped so Leaflet can pick them up) -->
<style>
.custom-tooltip {
  background: rgba(15, 25, 35, 0.92) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  border-radius: 6px !important;
  color: #e8eaf0 !important;
  font-size: 12px !important;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5) !important;
  padding: 6px 10px !important;
}
.custom-tooltip::before { display: none !important; }
.map-tooltip em { font-style: italic; color: #7ecfff; }
.map-tooltip span { color: rgba(255, 255, 255, 0.6); font-size: 11px; }
.leaflet-control-attribution {
  background: rgba(15, 25, 35, 0.7) !important;
  color: rgba(255, 255, 255, 0.4) !important;
  font-size: 10px !important;
}
.leaflet-control-attribution a { color: rgba(255, 255, 255, 0.5) !important; }
</style>
