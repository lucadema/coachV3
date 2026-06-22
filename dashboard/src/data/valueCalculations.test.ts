import { describe, expect, it } from 'vitest'
import {
  calculateValueMetrics,
  cleanHourlyRateInput,
  hourlyRateStorageKey,
  parseHourlyRate,
} from './valueCalculations'

describe('valueCalculations', () => {
  it('cleans and parses tolerant hourly-rate input', () => {
    expect(cleanHourlyRateInput('£45.50 per hour')).toBe('45.50')
    expect(parseHourlyRate('£45.50')).toBe(45.5)
    expect(parseHourlyRate('-10')).toBe(0)
    expect(parseHourlyRate('')).toBeNull()
  })

  it('calculates monthly and annual values from monthly minutes', () => {
    const metrics = calculateValueMetrics(720, 30)

    expect(metrics.monthlyHours).toBe(12)
    expect(metrics.monthlyValue).toBe(360)
    expect(metrics.annualValue).toBe(4320)
  })

  it('scopes hourly-rate storage keys by dashboard token', () => {
    expect(hourlyRateStorageKey('token-a')).not.toBe(hourlyRateStorageKey('token-b'))
  })
})
