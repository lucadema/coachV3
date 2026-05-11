import { describe, expect, it } from 'vitest'
import {
  isRefinedSynthesisWaitingForPathways,
  mapBackendToScreen,
  parsePathwayCards,
} from './sessionFlow'

describe('mapBackendToScreen', () => {
  it('maps classification to coaching', () => {
    expect(mapBackendToScreen({ stage: 'classification' })).toBe('coaching')
  })

  it('maps coaching to coaching', () => {
    expect(mapBackendToScreen({ stage: 'coaching' })).toBe('coaching')
  })

  it('maps synthesis to synthesis review', () => {
    expect(mapBackendToScreen({ stage: 'synthesis' })).toBe('synthesis_review')
  })

  it('maps pathways to pathways', () => {
    expect(mapBackendToScreen({ stage: 'pathways' })).toBe('pathways')
  })

  it('maps closure to feedback', () => {
    expect(mapBackendToScreen({ stage: 'closure' })).toBe('feedback')
  })

  it('maps unknown stages to coaching', () => {
    expect(mapBackendToScreen({ stage: 'fallback' })).toBe('coaching')
  })
})

describe('isRefinedSynthesisWaitingForPathways', () => {
  it('detects pathways preparing as awaiting pathways after refinement', () => {
    expect(isRefinedSynthesisWaitingForPathways({ stage: 'pathways', state: 'preparing' })).toBe(
      true,
    )
  })

  it('does not detect other pathways states as awaiting pathways after refinement', () => {
    expect(isRefinedSynthesisWaitingForPathways({ stage: 'pathways', state: 'presenting' })).toBe(
      false,
    )
  })
})

describe('parsePathwayCards', () => {
  it('parses markdown pathway headings into cards', () => {
    expect(
      parsePathwayCards(`
Intro text

## Build evidence
Use examples to test the idea.

## Change the conversation
Move the discussion into a different frame.
`),
    ).toEqual([
      { title: 'Build evidence', body: 'Use examples to test the idea.' },
      { title: 'Change the conversation', body: 'Move the discussion into a different frame.' },
    ])
  })

  it('returns an empty array when no markdown pathway headings are present', () => {
    expect(parsePathwayCards('A plain response without pathway headings.')).toEqual([])
  })
})
