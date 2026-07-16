const DB_NAME = 'yahaha-cover-studio-cache'
const DB_VERSION = 1
const STORE_NAME = 'entries'
// Increment when a backend refresh changes the source image contract. This prevents
// stale preview records from surviving an application update.
export const PREVIEW_CACHE_SCHEMA = 7
export const HISTORY_CACHE_SCHEMA = 2
const PREVIEW_MAX_ENTRIES = 30
const HISTORY_MAX_ENTRIES = 8
const PREVIEW_MAX_AGE = 7 * 24 * 60 * 60 * 1000
const HISTORY_MAX_AGE = 30 * 24 * 60 * 60 * 1000

interface CacheRecord<T = unknown> {
  id: string
  kind: 'preview' | 'history'
  schema: number
  baseKey: string
  capacity: number
  updatedAt: number
  lastUsedAt: number
  payload: T
}

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue }

export interface PreviewCacheRecord {
  schemaVersion: number
  cacheKey: string
  server: string
  library: string
  style: string
  coverStyleBase: string
  coverStyleVariant: string
  sourceMode: string
  titles: { zh: string; en: string }
  customTexts: Record<string, string>
  sources: Array<{
    id: string
    url: string
    type?: string
    label?: string
    serverId?: string
    libraryId?: string
    libraryKey?: string
    cacheVersion?: string
    updatedAt?: string
  }>
  customStaticLayout?: JsonValue
  bgColor?: string | null
  fontFaces: Record<string, { url: string; fontId?: string; fontFamily?: string; version?: string; sourceType?: string; subsetStatus?: string; charsetHash?: string }>
  createdAt: string
}

const memory = new Map<string, CacheRecord>()
let databasePromise: Promise<IDBDatabase | null> | null = null

function openDatabase(): Promise<IDBDatabase | null> {
  if (databasePromise) return databasePromise
  if (typeof indexedDB === 'undefined') return Promise.resolve(null)
  databasePromise = new Promise((resolve) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE_NAME)) db.createObjectStore(STORE_NAME, { keyPath: 'id' })
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => resolve(null)
  })
  return databasePromise
}

async function readAll(): Promise<CacheRecord[]> {
  const db = await openDatabase()
  if (!db) return [...memory.values()]
  return new Promise((resolve) => {
    const request = db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).getAll()
    request.onsuccess = () => resolve(Array.isArray(request.result) ? request.result : [])
    request.onerror = () => resolve([])
  })
}

async function writeRecord(record: CacheRecord) {
  memory.set(record.id, record)
  const db = await openDatabase()
  if (!db) return
  await new Promise<void>((resolve) => {
    try {
      const request = db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).put(record)
      request.onsuccess = () => resolve()
      request.onerror = () => {
        console.warn(`${record.kind} cache persistence failed`, request.error)
        resolve()
      }
    } catch (error) {
      console.warn(`${record.kind} cache persistence failed`, error)
      resolve()
    }
  })
}

function toJsonValue(value: unknown): JsonValue | undefined {
  if (value === null || typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return value
  if (Array.isArray(value)) return value.map(toJsonValue).filter((item): item is JsonValue => item !== undefined)
  if (!value || typeof value !== 'object') return undefined
  const plain: Record<string, JsonValue> = {}
  for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
    const next = toJsonValue(item)
    if (next !== undefined) plain[key] = next
  }
  return plain
}

export function createPreviewCacheRecord(cacheKey: string, payload: any): PreviewCacheRecord {
  const fontFaces = Object.entries(payload?.font_faces || {}).reduce((result, [key, source]) => {
    const value = typeof source === 'string' ? { url: source } : source as Record<string, unknown>
    const url = String(value?.url || '')
    if (!url) return result
    result[key] = {
      url,
      fontId: value.font_id ? String(value.font_id) : undefined,
      fontFamily: value.font_family ? String(value.font_family) : undefined,
      version: value.version ? String(value.version) : undefined,
      sourceType: value.source_type ? String(value.source_type) : undefined,
      subsetStatus: value.subset_status ? String(value.subset_status) : undefined,
      charsetHash: value.charset_hash ? String(value.charset_hash) : undefined,
    }
    return result
  }, {} as PreviewCacheRecord['fontFaces'])
  return {
    schemaVersion: PREVIEW_CACHE_SCHEMA,
    cacheKey,
    server: String(payload?.server || ''),
    library: String(payload?.library || ''),
    style: String(payload?.style || ''),
    coverStyleBase: String(payload?.cover_style_base || ''),
    coverStyleVariant: String(payload?.cover_style_variant || ''),
    sourceMode: String(payload?.source_mode || ''),
    titles: { zh: String(payload?.titles?.zh || ''), en: String(payload?.titles?.en || '') },
    customTexts: Object.entries(payload?.custom_texts || {}).reduce((result, [key, value]) => {
      result[String(key)] = String(value ?? '')
      return result
    }, {} as Record<string, string>),
    sources: Array.isArray(payload?.images) ? payload.images.map((item: any, index: number) => ({
      id: String(item?.slot ?? item?.id ?? index + 1),
      url: String(item?.src || ''),
      type: item?.kind ? String(item.kind) : undefined,
      label: item?.label ? String(item.label) : undefined,
      serverId: item?.server_id ? String(item.server_id) : undefined,
      libraryId: item?.library_id ? String(item.library_id) : undefined,
      libraryKey: item?.library_key ? String(item.library_key) : undefined,
      cacheVersion: item?.cache_version ? String(item.cache_version) : undefined,
      updatedAt: item?.updated_at ? String(item.updated_at) : undefined,
    })).filter((item: PreviewCacheRecord['sources'][number]) => item.url) : [],
    customStaticLayout: toJsonValue(payload?.custom_static_layout),
    bgColor: payload?.bg_color == null ? null : String(payload.bg_color),
    fontFaces,
    createdAt: new Date().toISOString(),
  }
}

export function previewCachePayload(record: PreviewCacheRecord) {
  return {
    server: record.server,
    library: record.library,
    style: record.style,
    cover_style_base: record.coverStyleBase,
    cover_style_variant: record.coverStyleVariant,
    source_mode: record.sourceMode,
    titles: record.titles,
    custom_texts: record.customTexts,
    images: record.sources.map((item, index) => ({ slot: Number(item.id) || index + 1, src: item.url, kind: item.type, label: item.label })),
    custom_static_layout: record.customStaticLayout,
    bg_color: record.bgColor,
    font_faces: Object.entries(record.fontFaces).reduce((result, [key, value]) => {
      result[key] = {
        url: value.url,
        font_id: value.fontId,
        font_family: value.fontFamily,
        version: value.version,
        source_type: value.sourceType,
        subset_status: value.subsetStatus,
        charset_hash: value.charsetHash,
      }
      return result
    }, {} as Record<string, unknown>),
  }
}

async function deleteRecords(ids: string[]) {
  ids.forEach((id) => memory.delete(id))
  const db = await openDatabase()
  if (!db || !ids.length) return
  await new Promise<void>((resolve) => {
    const transaction = db.transaction(STORE_NAME, 'readwrite')
    ids.forEach((id) => transaction.objectStore(STORE_NAME).delete(id))
    transaction.oncomplete = () => resolve()
    transaction.onerror = () => resolve()
  })
}

async function prune(kind: CacheRecord['kind'], maxEntries: number) {
  const records = (await readAll()).filter((item) => item.kind === kind).sort((a, b) => b.lastUsedAt - a.lastUsedAt)
  await deleteRecords(records.slice(maxEntries).map((item) => item.id))
}

export function stableCacheSignature(value: unknown): string {
  const normalize = (item: any): any => {
    if (Array.isArray(item)) return [...item].map(normalize).sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)))
    if (item && typeof item === 'object') return Object.keys(item).sort().reduce((result, key) => { result[key] = normalize(item[key]); return result }, {} as Record<string, unknown>)
    return item ?? ''
  }
  const text = JSON.stringify(normalize(value))
  let hash = 2166136261
  for (let index = 0; index < text.length; index += 1) hash = Math.imul(hash ^ text.charCodeAt(index), 16777619)
  return (hash >>> 0).toString(36)
}

export async function getPreviewCache<T>(baseKey: string, requiredItems: number): Promise<T | null> {
  const now = Date.now()
  const records = (await readAll()).filter((item) => item.kind === 'preview' && item.schema === PREVIEW_CACHE_SCHEMA && item.baseKey === baseKey && item.capacity >= requiredItems && now - item.updatedAt <= PREVIEW_MAX_AGE).sort((a, b) => a.capacity - b.capacity || b.updatedAt - a.updatedAt)
  const match = records[0] as CacheRecord<T> | undefined
  if (!match) return null
  const cachedPayload = match.payload as PreviewCacheRecord
  const hasPendingSubset = Object.values(cachedPayload?.fontFaces || {}).some((face) => face.subsetStatus === 'pending' || face.subsetStatus === 'building')
  if (hasPendingSubset) return null
  match.lastUsedAt = now
  memory.set(match.id, match)
  void writeRecord(match)
  return previewCachePayload(cachedPayload) as T
}

export async function setPreviewCache(baseKey: string, requiredItems: number, payload: unknown) {
  try {
    const now = Date.now()
    const record = createPreviewCacheRecord(baseKey, payload)
    await writeRecord({ id: `preview:v${PREVIEW_CACHE_SCHEMA}:${baseKey}:${requiredItems}`, kind: 'preview', schema: PREVIEW_CACHE_SCHEMA, baseKey, capacity: requiredItems, updatedAt: now, lastUsedAt: now, payload: record })
    await prune('preview', PREVIEW_MAX_ENTRIES)
  } catch (error) {
    console.warn('preview cache persistence failed', error)
  }
}

export async function invalidatePreviewCache(baseKey?: string) {
  const records = (await readAll()).filter((item) => item.kind === 'preview' && (!baseKey || item.baseKey === baseKey))
  await deleteRecords(records.map((item) => item.id))
}

export async function getHistoryCache<T>(baseKey: string): Promise<T | null> {
  const now = Date.now()
  const id = `history:v${HISTORY_CACHE_SCHEMA}:${baseKey}`
  const records = await readAll()
  const match = records.find((item) => item.id === id && item.schema === HISTORY_CACHE_SCHEMA && now - item.updatedAt <= HISTORY_MAX_AGE) as CacheRecord<T> | undefined
  if (!match) return null
  match.lastUsedAt = now
  memory.set(id, match)
  void writeRecord(match)
  return match.payload
}

export async function setHistoryCache<T>(baseKey: string, payload: T) {
  const now = Date.now()
  const persistedPayload = toJsonValue(payload)
  if (persistedPayload === undefined) return
  await writeRecord({ id: `history:v${HISTORY_CACHE_SCHEMA}:${baseKey}`, kind: 'history', schema: HISTORY_CACHE_SCHEMA, baseKey, capacity: Array.isArray(payload) ? payload.length : 1, updatedAt: now, lastUsedAt: now, payload: persistedPayload })
  await prune('history', HISTORY_MAX_ENTRIES)
}

export async function updateHistoryCache<T>(baseKey: string, updater: (items: T[]) => T[]) {
  const current = await getHistoryCache<T[]>(baseKey)
  await setHistoryCache(baseKey, updater(Array.isArray(current) ? current : []))
}
