import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  getDashboardApiBaseUrl,
  getDashboardToken,
  isDashboardTestMode,
  sanitizeDashboardToken,
} from './dashboardClient'

describe('dashboardClient', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('uses the dashboard API env var and falls back to the shared API base URL', () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://admin.example.com/')
    expect(getDashboardApiBaseUrl()).toBe('https://admin.example.com')

    vi.stubEnv('VITE_DASHBOARD_API_BASE_URL', 'https://dashboard-api.example.com/')
    expect(getDashboardApiBaseUrl()).toBe('https://dashboard-api.example.com')
  })

  it('extracts dashboard tokens from t and token query parameters', () => {
    expect(getDashboardToken('?t=AbC_1234567890-token_value')).toBe(
      'AbC_1234567890-token_value',
    )
    expect(getDashboardToken('?token=XyZ_1234567890-token_value')).toBe(
      'XyZ_1234567890-token_value',
    )
  })

  it('ignores invalid dashboard tokens', () => {
    expect(sanitizeDashboardToken('short')).toBeNull()
    expect(sanitizeDashboardToken('has spaces in token')).toBeNull()
  })

  it('treats test and test=true as visual test mode', () => {
    expect(isDashboardTestMode('?test')).toBe(true)
    expect(isDashboardTestMode('?test=true')).toBe(true)
    expect(isDashboardTestMode('?test=false')).toBe(false)
  })
})
