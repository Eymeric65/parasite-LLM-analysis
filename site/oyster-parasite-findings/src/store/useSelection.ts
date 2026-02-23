import { reactive } from 'vue'
import type { DisplayMode, Selection } from '../data/types'

// ─── Shared Reactive State ─────────────────────────────────────────────────────
//
// This module exposes a single reactive state object shared across all
// components that import it – a lightweight alternative to Pinia for this
// project's scope.

interface AppState {
  selection: Selection | null
  displayMode: DisplayMode
}

const state = reactive<AppState>({
  selection: null,
  displayMode: 'both',
})

// ─── Actions ───────────────────────────────────────────────────────────────────

/** Select or toggle-off a parasite / host species. */
function select(type: 'parasite' | 'host', species: string): void {
  if (
    state.selection?.type === type &&
    (state.selection as { species: string }).species === species
  ) {
    state.selection = null
  } else {
    state.selection = { type, species }
  }
}

/** Select or toggle-off a paper by document id. */
function selectPaper(documentId: number): void {
  if (state.selection?.type === 'paper' && state.selection.documentId === documentId) {
    state.selection = null
  } else {
    state.selection = { type: 'paper', documentId }
  }
}

function clearSelection(): void {
  state.selection = null
}

function setDisplayMode(mode: DisplayMode): void {
  state.displayMode = mode
}

// ─── Composable ────────────────────────────────────────────────────────────────

export function useSelection() {
  return { state, select, selectPaper, clearSelection, setDisplayMode }
}
