// ─── Species Color Utility ─────────────────────────────────────────────────────
//
// Deterministically maps a species name to a visually distinct HSL color.
// Using hue from a fast string hash ensures stable, spread-out colors.

function stringHash(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash)
}

export function speciesColor(name: string, alpha = 1): string {
  const hue = stringHash(name) % 360
  return `hsla(${hue}, 65%, 50%, ${alpha})`
}

export function speciesColorSolid(name: string): string {
  return speciesColor(name, 1)
}

export function speciesColorFaded(name: string): string {
  return speciesColor(name, 0.25)
}
