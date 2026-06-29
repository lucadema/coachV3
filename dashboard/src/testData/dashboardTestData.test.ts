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
    expect(first.action_ownership?.hearted).toHaveLength(4)
    expect(first.stuck_signal?.flags).toHaveLength(3)
    expect(first.stuck_signal?.combined_signals).toHaveLength(3)
  })

  it('keeps section totals consistent with the selected session count', () => {
    const data = createDashboardTestData({
      enterpriseName: 'NHS',
      pilotName: 'Demo Pilot',
      sessionCount: 200,
    })
    const problemTotal = sumCounts(data.problem_categories)
    const engagementTotal = sumCounts(data.engagement_signals)
    const flagTotal =
      data.value_unlocked.flag_to_organisation.yes_count +
      data.value_unlocked.flag_to_organisation.no_count
    const generatedTotal = sumCounts(data.action_ownership?.generated ?? [])
    const heartedTotal = sumCounts(data.action_ownership?.hearted ?? [])
    const stuckPreviouslyRaised =
      data.stuck_signal?.flags.find((flag) => flag.value === 'previously_raised')?.count ?? 0
    const combinedStuckTotal = sumCounts(data.stuck_signal?.combined_signals ?? [])

    expect(data.enterprise_name).toBe('NHS')
    expect(data.pilot_name).toBe('Demo Pilot')
    expect(problemTotal).toBe(200)
    expect(engagementTotal).toBe(200)
    expect(data.value_unlocked.qualifying_responses_count).toBe(200)
    expect(flagTotal).toBe(200)
    expect(heartedTotal).toBe(200)
    expect(generatedTotal).toBe(800)
    expect(data.stuck_signal?.classified_sessions_count).toBe(200)
    expect(data.stuck_signal?.flags.every((flag) => flag.denominator === 200)).toBe(true)
    expect(combinedStuckTotal).toBe(stuckPreviouslyRaised)
  })
})

function sumCounts(items: { count: number }[]): number {
  return items.reduce((sum, item) => sum + item.count, 0)
}
