import { describe, expect, it } from 'vitest'
import {
  buildEngagementSignalSegments,
  buildProblemCategoryBars,
  percentageOfTotal,
} from './dashboardTransforms'

describe('dashboardTransforms', () => {
  it('sorts problem categories by descending count and calculates percentages', () => {
    const bars = buildProblemCategoryBars([
      { value: 'a', label: 'A', count: 2 },
      { value: 'b', label: 'B', count: 6 },
      { value: 'c', label: 'C', count: 0 },
    ])

    expect(bars.map((bar) => bar.value)).toEqual(['b', 'a', 'c'])
    expect(bars[0].percentage).toBe(75)
    expect(bars[1].percentage).toBe(25)
    expect(bars[2].percentage).toBe(0)
  })

  it('handles zero totals safely', () => {
    expect(percentageOfTotal(4, 0)).toBe(0)
    expect(buildProblemCategoryBars([{ value: 'a', label: 'A', count: 0 }])[0].percentage).toBe(0)
  })

  it('keeps engagement signals in low-to-high risk order', () => {
    const segments = buildEngagementSignalSegments([
      { value: 'disengagement_risk', label: 'Disengagement risk', count: 2 },
      { value: 'no_visible_risk', label: 'No visible risk', count: 6 },
    ])

    expect(segments.map((segment) => segment.value)).toEqual([
      'no_visible_risk',
      'frustration_signal',
      'voice_suppression_signal',
      'disengagement_risk',
    ])
    expect(segments[0].percentage).toBe(75)
    expect(segments[3].percentage).toBe(25)
  })
})
