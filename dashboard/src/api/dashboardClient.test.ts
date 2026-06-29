import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  buildRedactedDashboardApiUrl,
  getDashboardApiBaseUrl,
  getDashboardTestOptions,
  getDashboardToken,
  isDashboardDebugMode,
  isDashboardTestMode,
  redactDashboardToken,
  sanitizeDashboardToken,
} from './dashboardClient'

describe('dashboardClient', () => {
  afterEach(() => {
    vi.restoreAllMocks()
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

  it('parses dashboard test options safely', () => {
    expect(
      getDashboardTestOptions(
        '?test&test_sessions=200&test_orgname=NHS&test_pilotname=Demo%20Pilot',
      ),
    ).toEqual({
      enterpriseName: 'NHS',
      pilotName: 'Demo Pilot',
      sessionCount: 200,
    })
    expect(getDashboardTestOptions('?test&testsessions=42').sessionCount).toBe(42)
    expect(getDashboardTestOptions('?test&test_sessions=not-a-number').sessionCount).toBe(50)
  })

  it('uses a bounded random session count when absent from test options', () => {
    const randomSpy = vi.spyOn(Math, 'random').mockReturnValue(0)
    expect(getDashboardTestOptions('?test').sessionCount).toBe(35)

    randomSpy.mockReturnValue(0.999)
    expect(getDashboardTestOptions('?test').sessionCount).toBe(120)
  })

  it('treats debug and debug=true as dashboard debug mode', () => {
    expect(isDashboardDebugMode('?debug')).toBe(true)
    expect(isDashboardDebugMode('?debug=true')).toBe(true)
    expect(isDashboardDebugMode('?debug=false')).toBe(false)
  })

  it('redacts dashboard tokens in debug output', () => {
    expect(redactDashboardToken('AbC_1234567890-token_value')).toBe(
      'AbC_1234... (26 chars)',
    )
    expect(
      buildRedactedDashboardApiUrl(
        'AbC_1234567890-token_value',
        'https://admin.example.com/',
      ),
    ).toBe('https://admin.example.com/dashboard/AbC_1234... (26 chars)')
  })
})
