import { describe, expect, it } from 'vitest'
import {
  buildCombinedStuckSignals,
  buildStuckFlagMetrics,
  percentageOfDenominator,
} from './stuckSignalTransforms'

describe('stuckSignalTransforms', () => {
  it('calculates percentages from explicit denominators', () => {
    expect(percentageOfDenominator(6, 8)).toBe(75)
    expect(percentageOfDenominator(5, 8)).toBe(63)
    expect(percentageOfDenominator(1, 0)).toBe(0)
  })

  it('keeps stuck flags and combined signals in dashboard order', () => {
    const flags = buildStuckFlagMetrics([
      {
        value: 'both_signals_present',
        label: 'Both signals present',
        count: 5,
        denominator: 8,
        description: 'Both.',
      },
      {
        value: 'previously_raised',
        label: 'Previously raised',
        count: 6,
        denominator: 8,
        description: 'Raised.',
      },
      {
        value: 'no_owner_identified',
        label: 'No owner identified',
        count: 6,
        denominator: 8,
        description: 'Owner.',
      },
    ])
    const combined = buildCombinedStuckSignals([
      {
        value: 'gave_up',
        label: 'Gave up',
        count: 1,
        denominator: 6,
        description: 'Gave up.',
      },
      {
        value: 'still_trying',
        label: 'Still trying',
        count: 4,
        denominator: 6,
        description: 'Still trying.',
      },
    ])

    expect(flags.map((flag) => flag.value)).toEqual([
      'previously_raised',
      'no_owner_identified',
      'both_signals_present',
    ])
    expect(flags.map((flag) => flag.percentage)).toEqual([75, 75, 63])
    expect(combined.map((signal) => signal.value)).toEqual(['still_trying', 'gave_up'])
    expect(combined[0].percentage).toBe(67)
  })
})
