import type { DashboardData, DashboardTestDataOptions } from '../types'

const DEFAULT_DASHBOARD_API_BASE_URL = 'http://127.0.0.1:8010'
const ACCESS_TOKEN_PATTERN = /^[A-Za-z0-9_-]{20,256}$/
const DEFAULT_TEST_SESSION_COUNT = 50
const MIN_TEST_SESSION_COUNT = 1
const MAX_TEST_SESSION_COUNT = 5000
const RANDOM_TEST_SESSION_MIN = 35
const RANDOM_TEST_SESSION_MAX = 120
const TEST_NAME_MAX_LENGTH = 120

export class DashboardApiError extends Error {
  readonly status: number | null
  readonly requestUrl: string

  constructor(message: string, status: number | null = null, requestUrl = '') {
    super(message)
    this.name = 'DashboardApiError'
    this.status = status
    this.requestUrl = requestUrl
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

export function redactDashboardToken(token: string | null | undefined): string {
  const normalized = String(token ?? '').trim()
  if (!normalized) {
    return 'missing'
  }

  return `${normalized.slice(0, 8)}... (${normalized.length} chars)`
}

export function buildRedactedDashboardApiUrl(
  token: string | null,
  baseUrl = getDashboardApiBaseUrl(),
): string | null {
  if (!token) {
    return null
  }

  return `${baseUrl.replace(/\/+$/, '')}/dashboard/${redactDashboardToken(token)}`
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

export function isDashboardDebugMode(search = window.location.search): boolean {
  const params = new URLSearchParams(search)
  if (!params.has('debug')) {
    return false
  }

  const value = params.get('debug')
  return value === '' || value === null || value.toLowerCase() === 'true'
}

export function getDashboardTestOptions(
  search = window.location.search,
): DashboardTestDataOptions {
  const params = new URLSearchParams(search)

  return {
    enterpriseName: sanitizeDashboardTestName(params.get('test_orgname')),
    pilotName: sanitizeDashboardTestName(params.get('test_pilotname')),
    sessionCount: parseDashboardTestSessionCount(params),
  }
}

export async function fetchDashboardData(
  token: string,
  baseUrl = getDashboardApiBaseUrl(),
): Promise<DashboardData> {
  const requestUrl = buildDashboardApiUrl(token, baseUrl)
  const response = await fetch(requestUrl, {
    headers: {
      Accept: 'application/json',
    },
  }).catch((error: unknown) => {
    throw new DashboardApiError(
      error instanceof Error ? error.message : 'Dashboard data could not be loaded.',
      null,
      requestUrl,
    )
  })

  if (!response.ok) {
    throw new DashboardApiError(
      'Dashboard data could not be loaded.',
      response.status,
      requestUrl,
    )
  }

  return (await response.json()) as DashboardData
}

function parseDashboardTestSessionCount(params: URLSearchParams): number {
  const rawValue = params.get('test_sessions') ?? params.get('testsessions')
  if (rawValue === null) {
    return randomTestSessionCount()
  }

  const normalized = rawValue.trim()
  if (!/^\d+$/.test(normalized)) {
    return DEFAULT_TEST_SESSION_COUNT
  }

  const value = Number(normalized)
  if (!Number.isSafeInteger(value) || value < MIN_TEST_SESSION_COUNT) {
    return DEFAULT_TEST_SESSION_COUNT
  }

  return Math.min(value, MAX_TEST_SESSION_COUNT)
}

function randomTestSessionCount(): number {
  const range = RANDOM_TEST_SESSION_MAX - RANDOM_TEST_SESSION_MIN + 1
  return RANDOM_TEST_SESSION_MIN + Math.floor(Math.random() * range)
}

function sanitizeDashboardTestName(value: string | null): string | undefined {
  const normalized = String(value ?? '')
    .replace(/\s+/g, ' ')
    .trim()

  if (!normalized) {
    return undefined
  }

  return normalized.slice(0, TEST_NAME_MAX_LENGTH)
}
