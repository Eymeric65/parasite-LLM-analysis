<script setup lang="ts">
import { computed, ref } from 'vue'
import { speciesColorSolid } from '../utils/color'
import {
  buildDocumentStats,
  buildSpeciesStats,
  formatDistance,
  sortDocumentStats,
  sortSpeciesStats,
} from '../utils/stats'
import type { SortKey } from '../utils/stats'
import { useSelection } from '../store/useSelection'
import type { Document, Finding } from '../data/types'

// ─── Props ────────────────────────────────────────────────────────────────────

const props = defineProps<{
  findings: Finding[]
  documents: Document[]
}>()

// ─── Store ────────────────────────────────────────────────────────────────────

const { state, select, selectPaper } = useSelection()

// ─── Tab & Sort State ─────────────────────────────────────────────────────────

type Tab = 'parasites' | 'hosts' | 'papers'

const activeTab = ref<Tab>('parasites')

// Each tab has its own independent sort key
const sortKeys = ref<Record<Tab, SortKey>>({
  parasites: 'alpha',
  hosts:     'alpha',
  papers:    'alpha',
})

const sortOptions: { key: SortKey; label: string; icon: string }[] = [
  { key: 'alpha',    label: 'A–Z',     icon: '🔤' },
  { key: 'count',    label: 'Count',   icon: '🔢' },
  { key: 'distance', label: 'Spread',  icon: '📍' },
]

// ─── Sorted & Derived Data ────────────────────────────────────────────────────

const parasiteStats = computed(() =>
  sortSpeciesStats(buildSpeciesStats(props.findings, 'parasite'), sortKeys.value.parasites),
)

const hostStats = computed(() =>
  sortSpeciesStats(buildSpeciesStats(props.findings, 'host'), sortKeys.value.hosts),
)

const documentStats = computed(() =>
  sortDocumentStats(buildDocumentStats(props.findings, props.documents), sortKeys.value.papers),
)

// ─── Helpers ──────────────────────────────────────────────────────────────────

function isSpeciesSelected(type: 'parasite' | 'host', species: string): boolean {
  return (
    state.selection?.type === type &&
    (state.selection as { species: string }).species === species
  )
}

function isPaperSelected(documentId: number): boolean {
  return state.selection?.type === 'paper' && state.selection.documentId === documentId
}

function shortTitle(refPaper: string): string {
  const cut = refPaper.search(/[,–—]/)
  return cut > 0 ? refPaper.slice(0, cut).trim() : refPaper
}

/** Secondary metric label shown underneath the item name, depending on sort. */
function speciesMetric(count: number, distKm: number): { label: string; value: string } | null {
  const sk = sortKeys.value[activeTab.value]
  if (sk === 'count')    return { label: 'findings', value: String(count) }
  if (sk === 'distance') return { label: 'spread',   value: formatDistance(distKm) }
  return null
}

function paperMetric(count: number, distKm: number): { label: string; value: string } | null {
  const sk = sortKeys.value.papers
  if (sk === 'count')    return { label: 'findings', value: String(count) }
  if (sk === 'distance') return { label: 'spread',   value: formatDistance(distKm) }
  return { label: 'findings', value: String(count) } // always show count for papers
}
</script>

<template>
  <aside class="left-panel">
    <!-- ── Tab Bar ──────────────────────────────────────────────── -->
    <nav class="tab-bar">
      <button
        v-for="tab in (['parasites', 'hosts', 'papers'] as Tab[])"
        :key="tab"
        class="tab-btn"
        :class="{ active: activeTab === tab }"
        @click="activeTab = tab"
      >
        <span class="tab-icon">
          {{ tab === 'parasites' ? '🦠' : tab === 'hosts' ? '🦪' : '📄' }}
        </span>
        {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
      </button>
    </nav>

    <!-- ── Sort Bar ─────────────────────────────────────────────── -->
    <div class="sort-bar">
      <span class="sort-label">Sort</span>
      <div class="sort-btns">
        <button
          v-for="opt in sortOptions"
          :key="opt.key"
          class="sort-btn"
          :class="{ active: sortKeys[activeTab] === opt.key }"
          :title="opt.label"
          @click="sortKeys[activeTab] = opt.key"
        >
          <span class="sort-icon">{{ opt.icon }}</span>
          {{ opt.label }}
        </button>
      </div>
    </div>

    <!-- ── Parasites Tab ────────────────────────────────────────── -->
    <section v-show="activeTab === 'parasites'" class="list-section">
      <div class="list-header">
        Parasites
        <span class="count-badge">{{ parasiteStats.length }}</span>
      </div>
      <ul class="item-list">
        <li
          v-for="s in parasiteStats"
          :key="s.name"
          class="list-item"
          :class="{ selected: isSpeciesSelected('parasite', s.name) }"
          @click="select('parasite', s.name)"
        >
          <span class="species-dot" :style="{ background: speciesColorSolid(s.name) }" />
          <span class="item-label">
            <span class="italic">{{ s.name }}</span>
            <span
              v-if="speciesMetric(s.count, s.maxDistanceKm)"
              class="metric-chip"
            >
              {{ speciesMetric(s.count, s.maxDistanceKm)!.value }}
              <span class="metric-unit">{{ speciesMetric(s.count, s.maxDistanceKm)!.label }}</span>
            </span>
          </span>
        </li>
      </ul>
    </section>

    <!-- ── Hosts Tab ───────────────────────────────────────────── -->
    <section v-show="activeTab === 'hosts'" class="list-section">
      <div class="list-header">
        Hosts
        <span class="count-badge">{{ hostStats.length }}</span>
      </div>
      <ul class="item-list">
        <li
          v-for="s in hostStats"
          :key="s.name"
          class="list-item"
          :class="{ selected: isSpeciesSelected('host', s.name) }"
          @click="select('host', s.name)"
        >
          <span class="species-dot" :style="{ background: speciesColorSolid(s.name) }" />
          <span class="item-label">
            <span class="italic">{{ s.name }}</span>
            <span
              v-if="speciesMetric(s.count, s.maxDistanceKm)"
              class="metric-chip"
            >
              {{ speciesMetric(s.count, s.maxDistanceKm)!.value }}
              <span class="metric-unit">{{ speciesMetric(s.count, s.maxDistanceKm)!.label }}</span>
            </span>
          </span>
        </li>
      </ul>
    </section>

    <!-- ── Papers Tab ──────────────────────────────────────────── -->
    <section v-show="activeTab === 'papers'" class="list-section">
      <div class="list-header">
        Papers
        <span class="count-badge">{{ documentStats.length }}</span>
      </div>
      <ul class="item-list">
        <li
          v-for="ds in documentStats"
          :key="ds.document.id"
          class="list-item paper-item"
          :class="{ selected: isPaperSelected(ds.document.id) }"
          @click="selectPaper(ds.document.id)"
        >
          <span class="paper-id">#{{ ds.document.id }}</span>
          <span class="item-label">
            {{ shortTitle(ds.document.reference_paper) }}
            <span class="metric-chip">
              {{ paperMetric(ds.count, ds.maxDistanceKm)!.value }}
              <span class="metric-unit">{{ paperMetric(ds.count, ds.maxDistanceKm)!.label }}</span>
              <template v-if="sortKeys.papers === 'distance' && ds.maxDistanceKm > 0">
                &nbsp;·&nbsp;{{ formatDistance(ds.maxDistanceKm) }} spread
              </template>
            </span>
          </span>
        </li>
      </ul>
    </section>
  </aside>
</template>

<style scoped>
.left-panel {
  width: 240px;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  background: #0f1923;
  border-right: 1px solid rgba(255, 255, 255, 0.07);
  overflow: hidden;
}

/* ── Tab Bar ─────────────────────────────────────────────────────── */

.tab-bar {
  display: flex;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  flex-shrink: 0;
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 9px 4px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: rgba(255, 255, 255, 0.4);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
  border-radius: 0;
  margin-bottom: -1px;
}

.tab-btn:hover {
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.04);
}

.tab-btn.active {
  color: #fff;
  border-bottom-color: rgba(74, 158, 255, 0.8);
}

.tab-icon { font-size: 12px; }

/* ── Sort Bar ────────────────────────────────────────────────────── */

.sort-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.015);
}

.sort-label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: rgba(255, 255, 255, 0.25);
  flex-shrink: 0;
}

.sort-btns {
  display: flex;
  gap: 3px;
  flex: 1;
}

.sort-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 3px 2px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  background: transparent;
  color: rgba(255, 255, 255, 0.35);
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
  white-space: nowrap;
}

.sort-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.65);
}

.sort-btn.active {
  background: rgba(74, 158, 255, 0.2);
  border-color: rgba(74, 158, 255, 0.5);
  color: #fff;
}

.sort-icon { font-size: 10px; }

/* ── List Section ────────────────────────────────────────────────── */

.list-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.list-header {
  display: flex;
  align-items: center;
  padding: 8px 14px 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
}

.count-badge {
  margin-left: auto;
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
}

/* ── List Items ──────────────────────────────────────────────────── */

.item-list {
  list-style: none;
  margin: 0;
  padding: 4px 0;
  overflow-y: auto;
  flex: 1;
}

.list-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 5px 14px;
  cursor: pointer;
  border-radius: 4px;
  margin: 1px 6px;
  transition: background 0.12s;
}

.list-item:hover   { background: rgba(255, 255, 255, 0.06); }
.list-item.selected {
  background: rgba(74, 158, 255, 0.18);
  outline: 1px solid rgba(74, 158, 255, 0.4);
}

/* ── Species dot ─────────────────────────────────────────────────── */

.species-dot {
  flex-shrink: 0;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-top: 3px;
}

/* ── Labels & metrics ────────────────────────────────────────────── */

.item-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.35;
  word-break: break-word;
  min-width: 0;
}

.list-item.selected .item-label { color: #fff; }

.italic { font-style: italic; }

.metric-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  font-size: 10px;
  font-style: normal;
  color: rgba(255, 255, 255, 0.38);
  font-weight: 600;
}

.list-item.selected .metric-chip { color: rgba(255, 255, 255, 0.6); }

.metric-unit {
  font-weight: 400;
  font-size: 9px;
  color: rgba(255, 255, 255, 0.25);
}

.list-item.selected .metric-unit { color: rgba(255, 255, 255, 0.45); }

/* ── Paper-specific ──────────────────────────────────────────────── */

.paper-item { align-items: flex-start; }

.paper-id {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.22);
  min-width: 22px;
  padding-top: 1px;
}
</style>
