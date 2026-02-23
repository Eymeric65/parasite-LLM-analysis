<script setup lang="ts">
import { computed, ref } from 'vue'
import { buildDocumentGroups, getFindingsByDocument, getFindingsByHost, getFindingsByParasite } from '../data/loader'
import { useSelection } from '../store/useSelection'
import type { Document, DocumentGroup, Finding } from '../data/types'

// ─── Props ────────────────────────────────────────────────────────────────────

const props = defineProps<{
  findings: Finding[]
  documents: Document[]
}>()

// ─── State ────────────────────────────────────────────────────────────────────

const { state, clearSelection } = useSelection()
const expandedScratchpads = ref<Set<number>>(new Set())

// ─── Derived Data ─────────────────────────────────────────────────────────────

const documentGroups = computed<DocumentGroup[]>(() => {
  if (!state.selection) return []

  let relevantFindings: Finding[]
  if (state.selection.type === 'parasite') {
    relevantFindings = getFindingsByParasite(props.findings, state.selection.species)
  } else if (state.selection.type === 'host') {
    relevantFindings = getFindingsByHost(props.findings, state.selection.species)
  } else {
    relevantFindings = getFindingsByDocument(props.findings, state.selection.documentId)
  }

  return buildDocumentGroups(relevantFindings, props.documents)
})

const totalFindings = computed<number>(() =>
  documentGroups.value.reduce((sum, g) => sum + g.findings.length, 0),
)

// ─── Helpers ──────────────────────────────────────────────────────────────────

function toggleScratchpad(docId: number): void {
  if (expandedScratchpads.value.has(docId)) {
    expandedScratchpads.value.delete(docId)
  } else {
    expandedScratchpads.value.add(docId)
  }
}

function isScratchpadExpanded(docId: number): boolean {
  return expandedScratchpads.value.has(docId)
}

function confidenceBadgeClass(score: string): string {
  switch (score?.toLowerCase()) {
    case 'high':   return 'badge-high'
    case 'medium': return 'badge-medium'
    case 'low':    return 'badge-low'
    default:       return 'badge-default'
  }
}

function formatCoords(lat: number | null, lng: number | null): string {
  if (lat === null || lng === null) return 'Coordinates unknown'
  return `${lat.toFixed(4)}°, ${lng.toFixed(4)}°`
}
</script>

<template>
  <aside class="info-panel" :class="{ empty: !state.selection }">
    <!-- Empty state -->
    <div v-if="!state.selection" class="empty-state">
      <div class="empty-icon">🔍</div>
      <p>Select a parasite or host<br />from the left panel</p>
    </div>

    <!-- Selection info -->
    <template v-else>
      <!-- Header -->
      <header class="panel-header">
        <div class="selection-meta">
          <span class="selection-type-badge" :class="state.selection.type">
            {{ state.selection.type }}
          </span>
          <span class="finding-count">{{ totalFindings }} finding{{ totalFindings !== 1 ? 's' : '' }}</span>
        </div>
        <h2 class="selection-title">
          <template v-if="state.selection.type === 'paper'">
            {{ documentGroups[0]?.document.reference_paper ?? 'Paper' }}
          </template>
          <template v-else>{{ state.selection.species }}</template>
        </h2>
        <button class="close-btn" @click="clearSelection" title="Clear selection">✕</button>
      </header>

      <!-- Document groups -->
      <div class="groups-container">
        <article
          v-for="group in documentGroups"
          :key="group.document.id"
          class="doc-group"
        >
          <!-- Paper name -->
          <div class="paper-info">
            <span class="paper-label">Paper</span>
            <p class="paper-title">{{ group.document.reference_paper }}</p>
          </div>

          <!-- Scratchpad (collapsible) -->
          <div v-if="group.document.scratchpad" class="scratchpad-section">
            <button
              class="scratchpad-toggle"
              @click="toggleScratchpad(group.document.id)"
            >
              <span>Analysis Notes</span>
              <span class="toggle-arrow" :class="{ expanded: isScratchpadExpanded(group.document.id) }">
                ▶
              </span>
            </button>
            <pre
              v-if="isScratchpadExpanded(group.document.id)"
              class="scratchpad-content"
            >{{ group.document.scratchpad }}</pre>
          </div>

          <!-- Findings for this paper -->
          <div class="findings-section">
            <span class="findings-label">
              {{ group.findings.length }} finding{{ group.findings.length !== 1 ? 's' : '' }} in this paper
            </span>
            <div
              v-for="(finding, idx) in group.findings"
              :key="idx"
              class="finding-card"
            >
              <div class="finding-row">
                <span class="field-label">Parasite</span>
                <span class="field-value italic">{{ finding.parasite_species }}</span>
              </div>
              <div class="finding-row">
                <span class="field-label">Host</span>
                <span class="field-value italic">{{ finding.host_species }}</span>
              </div>
              <div class="finding-row">
                <span class="field-label">Location</span>
                <span class="field-value">{{ finding.area }}, {{ finding.country }}</span>
              </div>
              <div class="finding-row">
                <span class="field-label">Coords</span>
                <span class="field-value coords">{{ formatCoords(finding.latitude, finding.longitude) }}</span>
              </div>
              <div class="finding-row">
                <span class="field-label">Confidence</span>
                <span class="confidence-badge" :class="confidenceBadgeClass(finding.confidence_score)">
                  {{ finding.confidence_score }}
                </span>
              </div>
            </div>
          </div>
        </article>
      </div>
    </template>
  </aside>
</template>

<style scoped>
/* ── Panel Shell ─────────────────────────────────────────────────── */

.info-panel {
  width: 280px;
  min-width: 240px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: #0f1923;
  border-left: 1px solid rgba(255, 255, 255, 0.07);
}

/* ── Empty State ─────────────────────────────────────────────────── */

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.3);
  font-size: 13px;
  text-align: center;
  padding: 24px;
}

.empty-icon {
  font-size: 32px;
  opacity: 0.5;
}

/* ── Header ──────────────────────────────────────────────────────── */

.panel-header {
  position: relative;
  padding: 16px 14px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.02);
}

.selection-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.selection-type-badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: 10px;
}

.selection-type-badge.parasite {
  background: rgba(255, 100, 100, 0.2);
  color: rgb(255, 150, 150);
  border: 1px solid rgba(255, 100, 100, 0.3);
}

.selection-type-badge.host {
  background: rgba(100, 200, 255, 0.2);
  color: rgb(130, 210, 255);
  border: 1px solid rgba(100, 200, 255, 0.3);
}

.selection-type-badge.paper {
  background: rgba(170, 120, 255, 0.2);
  color: rgb(190, 150, 255);
  border: 1px solid rgba(170, 120, 255, 0.3);
}

.finding-count {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.selection-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  font-style: italic;
  color: #e8eaf0;
  line-height: 1.3;
  padding-right: 24px;
}

.close-btn {
  position: absolute;
  top: 14px;
  right: 12px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 2px 5px;
  border-radius: 3px;
  transition: color 0.15s, background 0.15s;
}

.close-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

/* ── Groups ──────────────────────────────────────────────────────── */

.groups-container {
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.doc-group {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.doc-group:last-child {
  border-bottom: none;
}

/* ── Paper Info ──────────────────────────────────────────────────── */

.paper-info {
  margin-bottom: 10px;
}

.paper-label {
  display: block;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.35);
  margin-bottom: 3px;
}

.paper-title {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.45;
}

/* ── Scratchpad ──────────────────────────────────────────────────── */

.scratchpad-section {
  margin-bottom: 10px;
}

.scratchpad-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 5px 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
}

.scratchpad-toggle:hover {
  background: rgba(255, 255, 255, 0.08);
}

.toggle-arrow {
  font-size: 9px;
  transition: transform 0.2s;
  display: inline-block;
}

.toggle-arrow.expanded {
  transform: rotate(90deg);
}

.scratchpad-content {
  margin: 6px 0 0;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: hidden;
  max-height: 300px;
  overflow-y: auto;
}

/* ── Findings ────────────────────────────────────────────────────── */

.findings-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.findings-label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.3);
}

.finding-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 6px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.finding-row {
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.field-label {
  flex-shrink: 0;
  width: 60px;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.35);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field-value {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.3;
}

.field-value.italic {
  font-style: italic;
}

.field-value.coords {
  font-family: monospace;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.45);
}

/* ── Confidence Badge ────────────────────────────────────────────── */

.confidence-badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 8px;
}

.badge-high   { background: rgba(60, 200, 100, 0.2); color: rgb(100, 220, 130); border: 1px solid rgba(60, 200, 100, 0.3); }
.badge-medium { background: rgba(255, 180, 40, 0.2); color: rgb(255, 195, 80);  border: 1px solid rgba(255, 180, 40, 0.3); }
.badge-low    { background: rgba(255, 90, 90, 0.2);  color: rgb(255, 130, 130); border: 1px solid rgba(255, 90, 90, 0.3);  }
.badge-default{ background: rgba(255, 255, 255, 0.1); color: rgba(255, 255, 255, 0.5); }
</style>
