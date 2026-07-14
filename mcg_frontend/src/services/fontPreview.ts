type FontSource = string | { url?: string; font_family?: string; version?: string; font_id?: string }

const pending = new Map<string, Promise<boolean>>()

export async function loadPreviewFont(name: string, source?: FontSource): Promise<boolean> {
  const url = typeof source === 'string' ? source : source?.url
  if (!url || typeof FontFace === 'undefined' || typeof document === 'undefined') return false
  const family = typeof source === 'string' ? name : (source.font_family || name)
  const key = `${family}:${source && typeof source !== 'string' ? source.version || source.font_id || '' : ''}:${url}`
  const existing = pending.get(key)
  if (existing) return existing
  const task = new FontFace(family, `url(${url})`).load()
    .then(async (font) => {
      document.fonts.add(font)
      await document.fonts.load(`16px "${family}"`)
      return true
    })
    .catch((error) => {
      console.warn(`preview font unavailable: ${name}`, error)
      return false
    })
  pending.set(key, task)
  return task
}

export async function loadPreviewFontFaces(faces?: Record<string, FontSource>, familyForKey: (key: string) => string = (key) => key) {
  return Promise.all(Object.entries(faces || {}).map(([key, source]) => loadPreviewFont(familyForKey(key), source)))
}
