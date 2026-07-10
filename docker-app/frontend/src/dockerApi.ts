import type { MediaCoverGeneratorConfig, PluginApi } from './types/plugin'

type ApiEnvelope<T = any> = {
  code: number
  msg?: string
  data?: T
}

async function request<T = any>(method: 'GET' | 'POST' | 'DELETE', path: string, data?: any): Promise<T> {
  const normalized = normalizePluginPath(path, method === 'GET' ? data : undefined)
  const response = await fetch(normalized, {
    method,
    headers: method === 'GET' ? undefined : { 'Content-Type': 'application/json' },
    body: method === 'GET' ? undefined : JSON.stringify(data ?? {}),
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || response.statusText)
  }
  return response.json() as Promise<T>
}

function normalizePluginPath(path: string, params?: Record<string, any>) {
  let normalized = path
  if (!/^https?:\/\//.test(normalized)) {
    if (normalized.startsWith('/api/')) {
      // already normalized
    } else if (normalized.startsWith('plugin/MediaCoverGenerator/')) {
      normalized = `/api/${normalized}`
    } else if (normalized.startsWith('/plugin/MediaCoverGenerator/')) {
      normalized = `/api${normalized}`
    } else {
      normalized = normalized.startsWith('/') ? normalized : `/${normalized}`
    }
  }
  if (!params || Object.keys(params).length === 0) return normalized
  const url = new URL(normalized, window.location.origin)
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    if (Array.isArray(value)) {
      value.forEach((item) => url.searchParams.append(key, String(item)))
      return
    }
    url.searchParams.set(key, String(value))
  })
  return /^https?:\/\//.test(normalized) ? url.toString() : `${url.pathname}${url.search}`
}

export const dockerApi: PluginApi = {
  get: (path, params) => request('GET', path, params),
  post: (path, data) => request('POST', path, data),
  delete: (path, data) => request('DELETE', path, data),
}

export async function loadDockerConfig(): Promise<Partial<MediaCoverGeneratorConfig>> {
  const resp = await request<ApiEnvelope<{ config: Partial<MediaCoverGeneratorConfig> }>>(
    'GET',
    'plugin/MediaCoverGenerator/config',
  )
  return resp.data?.config || {}
}
