import { describe, expect, it } from 'vitest'
import {
  buildActionOwnershipComparison,
  buildActionOwnershipTiles,
} from './actionOwnershipTransforms'

describe('actionOwnershipTransforms', () => {
  it('builds hearted ownership tiles with percentages and stable ordering', () => {
    const tiles = buildActionOwnershipTiles([
      { value: 'escalation_required', label: 'Escalation needed', count: 6 },
      { value: 'self_actionable', label: 'Self-actionable', count: 1 },
      { value: 'system_change', label: 'System change', count: 0 },
      { value: 'disengagement_signal', label: 'Absorbing it', count: 1 },
    ])

    expect(tiles.map((tile) => tile.value)).toEqual([
      'self_actionable',
      'escalation_required',
      'disengagement_signal',
    ])
    expect(tiles.map((tile) => tile.percentage)).toEqual([13, 75, 13])
  })

  it('compares generated and hearted ownership distributions independently', () => {
    const comparison = buildActionOwnershipComparison({
      generated: [
        { value: 'self_actionable', label: 'Self-actionable', count: 7 },
        { value: 'escalation_required', label: 'Escalation needed', count: 17 },
        { value: 'disengagement_signal', label: 'Absorbing it', count: 2 },
      ],
      hearted: [
        { value: 'self_actionable', label: 'Self-actionable', count: 1 },
        { value: 'escalation_required', label: 'Escalation needed', count: 6 },
        { value: 'disengagement_signal', label: 'Absorbing it', count: 1 },
      ],
    })

    expect(comparison[0]).toMatchObject({
      value: 'self_actionable',
      generatedPercentage: 27,
      heartedPercentage: 13,
    })
    expect(comparison[1]).toMatchObject({
      value: 'escalation_required',
      generatedPercentage: 65,
      heartedPercentage: 75,
    })
  })
})
