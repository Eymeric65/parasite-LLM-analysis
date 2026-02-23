import type { Document, DocumentGroup, Finding } from './types'

// ─── JSONL Fetching ────────────────────────────────────────────────────────────
//
// Paths are prefixed with import.meta.env.BASE_URL so the app works both
// locally (base = '/') and on GitHub Pages (base = '/<repo-name>/').

async function fetchJsonl<T>(path: string): Promise<T[]> {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '') // strip trailing slash
  const url  = `${base}/${path}`
  const res  = await fetch(url)
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.statusText}`)
  const text = await res.text()
  return text
    .trim()
    .split('\n')
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line) as T)
}

// ─── Public Loaders ────────────────────────────────────────────────────────────

export async function loadFindings(): Promise<Finding[]> {
  return fetchJsonl<Finding>('database/findings_final.jsonl')
}

export async function loadDocuments(): Promise<Document[]> {
  return fetchJsonl<Document>('database/documents.jsonl')
}

// ─── Derived Data Helpers ──────────────────────────────────────────────────────

/**
 * Deduplicate species names case-insensitively, keeping the first-encountered
 * capitalisation as the canonical display form.
 */
function uniqueSpecies(names: string[]): string[] {
  const seen = new Map<string, string>() // lowercase key → canonical display form
  for (const name of names) {
    const key = name.toLowerCase()
    if (!seen.has(key)) seen.set(key, name)
  }
  return [...seen.values()].sort((a, b) =>
    a.toLowerCase().localeCompare(b.toLowerCase()),
  )
}

export function getUniqueParasites(findings: Finding[]): string[] {
  return uniqueSpecies(findings.map((f) => f.parasite_species))
}

export function getUniqueHosts(findings: Finding[]): string[] {
  return uniqueSpecies(findings.map((f) => f.host_species))
}

export function getFindingsByParasite(findings: Finding[], species: string): Finding[] {
  const lc = species.toLowerCase()
  return findings.filter((f) => f.parasite_species.toLowerCase() === lc)
}

export function getFindingsByHost(findings: Finding[], species: string): Finding[] {
  const lc = species.toLowerCase()
  return findings.filter((f) => f.host_species.toLowerCase() === lc)
}

export function getFindingsByDocument(findings: Finding[], documentId: number): Finding[] {
  return findings.filter((f) => f.document_id === documentId)
}

/**
 * Given a set of relevant findings, group them by document_id and attach
 * the corresponding Document metadata for display in the info panel.
 */
export function buildDocumentGroups(
  findings: Finding[],
  documents: Document[],
): DocumentGroup[] {
  const docMap = new Map<number, Document>(documents.map((d) => [d.id, d]))
  const groupMap = new Map<number, Finding[]>()

  for (const finding of findings) {
    const arr = groupMap.get(finding.document_id) ?? []
    arr.push(finding)
    groupMap.set(finding.document_id, arr)
  }

  const groups: DocumentGroup[] = []
  for (const [docId, docFindings] of groupMap.entries()) {
    const document = docMap.get(docId)
    if (document) {
      groups.push({ document, findings: docFindings })
    }
  }

  // Sort by document id for stable ordering
  groups.sort((a, b) => a.document.id - b.document.id)
  return groups
}
