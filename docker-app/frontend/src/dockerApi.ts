import type { MediaCoverGeneratorConfig, PluginApi } from './types/plugin'

type ApiEnvelope<T = any> = {
  code: number
  msg?: string
  data?: T
}

export type AuthStatus = {
  configured: boolean
  authenticated: boolean
  username: string
}

export type AuthSession = {
  authenticated: boolean
  username: string
  token: string
}

const AUTH_TOKEN_KEY = 'yahaha_auth_token'

export function getAuthToken() {
  return typeof window === 'undefined' ? '' : window.localStorage.getItem(AUTH_TOKEN_KEY) || ''
}

export function setAuthToken(token: string) {
  if (typeof window === 'undefined') return
  if (token) window.localStorage.setItem(AUTH_TOKEN_KEY, token)
  else window.localStorage.removeItem(AUTH_TOKEN_KEY)
}

async function request<T = any>(method: 'GET' | 'POST' | 'DELETE', path: string, data?: any): Promise<T> {
  const normalized = normalizePluginPath(path, method === 'GET' ? data : undefined)
  const token = getAuthToken()
  const headers: Record<string, string> = {}
  if (method !== 'GET') headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(normalized, {
    method,
    headers,
    body: method === 'GET' ? undefined : JSON.stringify(data ?? {}),
    credentials: 'same-origin',
  })
  if (!response.ok) {
    const raw = await response.text()
    let detail = raw || response.statusText
    try {
      const payload = JSON.parse(raw)
      detail = payload.detail || payload.message || payload.code || detail
    } catch { /* plain-text error response */ }
    if (response.status === 401 && typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('yahaha-auth-required'))
    }
    throw new Error(detail)
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

export function loadAuthStatus() {
  return request<AuthStatus>('GET', '/api/auth/status')
}

export async function setupDockerAuth(username: string, password: string) {
  const session = await request<AuthSession>('POST', '/api/auth/setup', { username, password })
  setAuthToken(session.token)
  return session
}

export async function loginDocker(username: string, password: string) {
  const session = await request<AuthSession>('POST', '/api/auth/login', { username, password })
  setAuthToken(session.token)
  return session
}

export async function logoutDocker() {
  try {
    await request('POST', '/api/auth/logout')
  } finally {
    setAuthToken('')
  }
}
