import type { DashboardData } from '../types'

const DEFAULT_DASHBOARD_API_BASE_URL = 'http://127.0.0.1:8010'
const ACCESS_TOKEN_PATTERN = /^[A-Za-z0-9_-]{20,256}$/

export class DashboardApiError extends Error {
  readonly status: number | null

  constructor(message: string, status: number | null = null) {
    super(message)
    this.name = 'DashboardApiError'
    this.status = status
  }
}

export function getDashboardApiBaseUrl(): string {
  return (
    import.meta.env.VITE_DASHBOARD_API_BASE_URL ||
    import.meta.env.VITE_API_BASE_URL ||
    DEFAULT_DASHBOARD_API_BASE_URL
  ).replace(/\/+$/, '')
}

export function buildDashboardApiUrl(token: string, baseUrl = getDashboardApiBaseUrl()): string {
  return `${baseUrl.replace(/\/+$/, '')}/dashboard/${encodeURIComponent(token)}`
}

export function sanitizeDashboardToken(value: string | null | undefined): string | null {
  const normalized = String(value ?? '').trim()
  if (!normalized || !ACCESS_TOKEN_PATTERN.test(normalized)) {
    return null
  }

  return normalized
}

export function getDashboardToken(search = window.location.search): string | null {
  const params = new URLSearchParams(search)
  return sanitizeDashboardToken(params.get('t') ?? params.get('token'))
}

export function isDashboardTestMode(search = window.location.search): boolean {
  const params = new URLSearchParams(search)
  if (!params.has('test')) {
    return false
  }

  const value = params.get('test')
  return value === '' || value === null || value.toLowerCase() === 'true'
}

export async function fetchDashboardData(
  token: string,
  baseUrl = getDashboardApiBaseUrl(),
): Promise<DashboardData> {
  const response = await fetch(buildDashboardApiUrl(token, baseUrl), {
    headers: {
      Accept: 'application/json',
    },
  }).catch((error: unknown) => {
    throw new DashboardApiError(
      error instanceof Error ? error.message : 'Dashboard data could not be loaded.',
    )
  })

  if (!response.ok) {
    throw new DashboardApiError('Dashboard data could not be loaded.', response.status)
  }

  return (await response.json()) as DashboardData
}
