import { describe, expect, it } from 'vitest'
import { createDashboardTestData } from './dashboardTestData'

describe('dashboardTestData', () => {
  it('generates deterministic meaningful dashboard sample data', () => {
    const first = createDashboardTestData()
    const second = createDashboardTestData()

    expect(first).toEqual(second)
    expect(first.available).toBe(true)
    expect(first.problem_categories).toHaveLength(6)
    expect(first.engagement_signals).toHaveLength(4)
    expect(first.value_unlocked.qualifying_responses_count).toBeGreaterThan(0)
    expect(first.value_unlocked.monthly_minutes).toBeGreaterThan(0)
  })
})
