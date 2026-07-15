import { applyPreviewFontFamily, clearPreviewFontFamily } from '../constants/fonts'

export interface PreviewFontInfo {
  url?: string
  font_family?: string
  version?: string
  font_id?: string
  source_type?: 'subset' | 'original' | 'remote' | 'disabled'
  subset_status?: 'ready' | 'pending' | 'building' | 'failed' | 'disabled'
  charset_hash?: string
}

export type FontSource = string | PreviewFontInfo

const pending = new Map<string, Promise<boolean>>()
const loaded = new Set<string>()

export function getPreviewFontInfo(source?: FontSource): PreviewFontInfo | null {
  if (!source) return null
  if (typeof source === 'string') return { url: source, source_type: 'remote', version: source }
  return source.url ? source : null
}

function fallbackDynamicFamily(alias: string, source: PreviewFontInfo) {
  const id = String(source.font_id || alias).replace(/[^a-zA-Z0-9_-]/g, '_')
  const version = String(source.version || source.charset_hash || 'original').replace(/[^a-zA-Z0-9_-]/g, '_')
  return `YahahaPreview_${id}_${version}`
}

export async function ensurePreviewFont(alias: string, source?: FontSource): Promise<boolean> {
  const info = getPreviewFontInfo(source)
  const url = info?.url
  if (!url || typeof FontFace === 'undefined' || typeof document === 'undefined') {
    clearPreviewFontFamily(alias)
    return false
  }
  const family = info.font_family || fallbackDynamicFamily(alias, info)
  const key = `${family}:${info.version || info.font_id || ''}:${url}`
  if (loaded.has(key)) {
    applyPreviewFontFamily(alias, family)
    return true
  }
  const existing = pending.get(key)
  if (existing) return existing
  // Quote URLs so plugin query strings and encoded file names are accepted by
  // the CSS parser used by FontFace on Safari as well as Chromium.
  const escapedUrl = String(url).replace(/\\/g, '\\\\').replace(/"/g, '\\"')
  const task = new FontFace(family, `url("${escapedUrl}")`, { display: 'swap' }).load()
    .then(async (font) => {
      document.fonts.add(font)
      await document.fonts.load(`16px "${family}"`)
      loaded.add(key)
      // Do not expose the dynamic family until it has loaded. This prevents a
      // transient 404 from leaving the preview pinned to an unusable family.
      applyPreviewFontFamily(alias, family)
      return true
    })
    .catch((error) => {
      clearPreviewFontFamily(alias)
      console.warn(`preview font unavailable: ${alias}`, error)
      return false
    })
    .finally(() => pending.delete(key))
  pending.set(key, task)
  return task
}

export async function loadPreviewFontFaces(faces?: Record<string, FontSource>) {
  return Promise.all(Object.entries(faces || {}).map(([key, source]) => ensurePreviewFont(key, source)))
}
