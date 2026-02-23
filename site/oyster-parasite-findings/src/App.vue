<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { loadDocuments, loadFindings } from './data/loader'
import type { Document, Finding } from './data/types'
import LeftPanel from './components/LeftPanel.vue'
import MapView from './components/MapView.vue'
import InfoPanel from './components/InfoPanel.vue'
import LayerToggle from './components/LayerToggle.vue'

// ─── Data Loading ─────────────────────────────────────────────────────────────

const findings  = ref<Finding[]>([])
const documents = ref<Document[]>([])
const loading   = ref(true)
const error     = ref<string | null>(null)

onMounted(async () => {
  try {
    ;[findings.value, documents.value] = await Promise.all([
      loadFindings(),
      loadDocuments(),
    ])
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load data'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="app-shell">
    <!-- Loading / Error overlays -->
    <div v-if="loading" class="overlay">
      <div class="spinner" />
      <span>Loading database…</span>
    </div>
    <div v-else-if="error" class="overlay error">
      <span>⚠ {{ error }}</span>
    </div>

    <!-- Main layout: Left | Map | Right -->
    <template v-else>
      <LeftPanel :findings="findings" :documents="documents" />

      <!-- Map column: toggle floats above the map -->
      <div class="map-column">
        <MapView :findings="findings" />
        <div class="toggle-overlay">
          <LayerToggle />
        </div>
      </div>

      <InfoPanel :findings="findings" :documents="documents" />
    </template>
  </div>
</template>

<style scoped>
.app-shell {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  background: #0f1923;
}

/* ── Map Column ──────────────────────────────────────────────────── */

.map-column {
  flex: 1;
  position: relative;
  display: flex;
  min-width: 0;
}

.toggle-overlay {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  pointer-events: all;
}

/* ── Overlays ────────────────────────────────────────────────────── */

.overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  background: #0f1923;
  z-index: 9999;
}

.overlay.error {
  color: rgb(255, 130, 130);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: rgba(74, 158, 255, 0.8);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
