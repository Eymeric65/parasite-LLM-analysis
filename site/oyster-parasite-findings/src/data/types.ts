// ─── Domain Types ─────────────────────────────────────────────────────────────

export interface Finding {
  document_id: number
  parasite_species: string
  host_species: string
  country: string
  area: string
  latitude: number | null
  longitude: number | null
  confidence_score: string
}

export interface Document {
  id: number
  source_file: string
  reference_paper: string
  scratchpad: string
}

// ─── UI / State Types ──────────────────────────────────────────────────────────

export type DisplayMode = 'parasites' | 'hosts' | 'both'

export type SelectionType = 'parasite' | 'host' | 'paper'

/** Discriminated union – each variant carries only its relevant payload. */
export type Selection =
  | { type: 'parasite'; species: string }
  | { type: 'host';     species: string }
  | { type: 'paper';   documentId: number }

// ─── Derived / Convenience Types ───────────────────────────────────────────────

export interface DocumentGroup {
  document: Document
  findings: Finding[]
}
