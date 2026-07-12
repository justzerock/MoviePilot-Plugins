const DB_NAME = 'yahaha-cover-studio-cache'
const DB_VERSION = 1
const STORE_NAME = 'entries'
export const PREVIEW_CACHE_SCHEMA = 1
export const HISTORY_CACHE_SCHEMA = 1
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
    const request = db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).put(record)
    request.onsuccess = () => resolve()
    request.onerror = () => resolve()
  })
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
  match.lastUsedAt = now
  memory.set(match.id, match)
  void writeRecord(match)
  return match.payload
}

export async function setPreviewCache<T>(baseKey: string, requiredItems: number, payload: T) {
  const now = Date.now()
  await writeRecord({ id: `preview:v${PREVIEW_CACHE_SCHEMA}:${baseKey}:${requiredItems}`, kind: 'preview', schema: PREVIEW_CACHE_SCHEMA, baseKey, capacity: requiredItems, updatedAt: now, lastUsedAt: now, payload })
  await prune('preview', PREVIEW_MAX_ENTRIES)
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
  await writeRecord({ id: `history:v${HISTORY_CACHE_SCHEMA}:${baseKey}`, kind: 'history', schema: HISTORY_CACHE_SCHEMA, baseKey, capacity: Array.isArray(payload) ? payload.length : 1, updatedAt: now, lastUsedAt: now, payload })
  await prune('history', HISTORY_MAX_ENTRIES)
}

export async function updateHistoryCache<T>(baseKey: string, updater: (items: T[]) => T[]) {
  const current = await getHistoryCache<T[]>(baseKey)
  await setHistoryCache(baseKey, updater(Array.isArray(current) ? current : []))
}
