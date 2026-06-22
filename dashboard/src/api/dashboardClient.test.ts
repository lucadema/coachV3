import { describe, expect, it } from 'vitest'
import {
  getDashboardToken,
  isDashboardTestMode,
  sanitizeDashboardToken,
} from './dashboardClient'

describe('dashboardClient', () => {
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
