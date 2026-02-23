<script setup lang="ts">
import { useSelection } from '../store/useSelection'
import type { DisplayMode } from '../data/types'

// ─── State ────────────────────────────────────────────────────────────────────

const { state, setDisplayMode } = useSelection()

const modes: { value: DisplayMode; label: string }[] = [
  { value: 'parasites', label: 'Parasites' },
  { value: 'both',      label: 'Both'      },
  { value: 'hosts',     label: 'Hosts'     },
]
</script>

<template>
  <div class="layer-toggle">
    <button
      v-for="mode in modes"
      :key="mode.value"
      class="toggle-btn"
      :class="{ active: state.displayMode === mode.value }"
      @click="setDisplayMode(mode.value)"
    >
      {{ mode.label }}
    </button>
  </div>
</template>

<style scoped>
.layer-toggle {
  display: flex;
  gap: 4px;
  padding: 6px 10px;
  background: rgba(20, 30, 48, 0.92);
  border-radius: 8px;
  backdrop-filter: blur(6px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.toggle-btn {
  padding: 5px 14px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 5px;
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.toggle-btn.active {
  background: rgba(74, 158, 255, 0.3);
  border-color: rgba(74, 158, 255, 0.7);
  color: #fff;
}
</style>
