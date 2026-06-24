import { describe, expect, it } from 'vitest'
import { mapBackendToScreen, parsePathwayCards, stepFromBackendSession } from './stages'

describe('stage mapping', () => {
  it('maps backend stages to frontend steps', () => {
    expect(stepFromBackendSession({ stage: 'classification', state: 'evaluating' })).toBe(
      'coaching',
    )
    expect(stepFromBackendSession({ stage: 'synthesis', state: 'validating' })).toBe(
      'synthesis_review',
    )
    expect(stepFromBackendSession({ stage: 'pathways', state: 'presenting' })).toBe('pathways')
    expect(stepFromBackendSession({ stage: 'closure', state: 'completed' })).toBe(
      'feedback_query',
    )
  })

  it('uses closed for cancelled non-closure sessions', () => {
    expect(mapBackendToScreen({ stage: 'coaching', cancelled: true })).toBe('closed')
  })
})

describe('pathway parsing', () => {
  it('parses markdown heading sections into pathway cards', () => {
    expect(
      parsePathwayCards('## Path A\nOrientation: Try A\n\nConditions: When A\n\n## Path B\nTry B'),
    ).toEqual([
      { title: 'Path A', body: 'Orientation: Try A\n\nConditions: When A' },
      { title: 'Path B', body: 'Try B' },
    ])
  })

  it('returns no cards when headings are absent', () => {
    expect(parsePathwayCards('No structured pathways yet')).toEqual([])
  })
})
