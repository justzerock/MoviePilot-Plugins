import { applyPreviewFontFamily, clearPreviewFontFamily, getTemplateFontFaceName } from '../constants/fonts'

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

export function applyPreviewFont(alias: string, source?: FontSource) {
  const info = getPreviewFontInfo(source)
  if (!info) {
    clearPreviewFontFamily(alias)
    return getTemplateFontFaceName(alias)
  }
  const family = info.font_family || fallbackDynamicFamily(alias, info)
  applyPreviewFontFamily(alias, family)
  return family
}

export async function ensurePreviewFont(alias: string, source?: FontSource): Promise<boolean> {
  const info = getPreviewFontInfo(source)
  const url = info?.url
  if (!url || typeof FontFace === 'undefined' || typeof document === 'undefined') {
    clearPreviewFontFamily(alias)
    return false
  }
  const family = applyPreviewFont(alias, info)
  const key = `${family}:${info.version || info.font_id || ''}:${url}`
  const existing = pending.get(key)
  if (existing) return existing
  const task = new FontFace(family, `url(${url})`).load()
    .then(async (font) => {
      document.fonts.add(font)
      await document.fonts.load(`16px "${family}"`)
      return true
    })
    .catch((error) => {
      clearPreviewFontFamily(alias)
      console.warn(`preview font unavailable: ${alias}`, error)
      return false
    })
  pending.set(key, task)
  return task
}

export async function loadPreviewFontFaces(faces?: Record<string, FontSource>) {
  return Promise.all(Object.entries(faces || {}).map(([key, source]) => ensurePreviewFont(key, source)))
}
