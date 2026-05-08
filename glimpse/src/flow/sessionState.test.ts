import { describe, expect, it } from 'vitest'
import {
  MISSING_SESSION_NOTICE,
  buildBackendTurnStateUpdate,
  buildMissingSessionResetState,
} from './sessionState'

describe('buildBackendTurnStateUpdate', () => {
  it('maps a coaching backend response to the coaching screen', () => {
    const update = buildBackendTurnStateUpdate({
      session: { stage: 'coaching', state: 'guiding' },
      coach_message: 'Tell me more.',
    })

    expect(update).toMatchObject({
      uiScreen: 'coaching',
      coachMessage: 'Tell me more.',
      sessionView: { stage: 'coaching', state: 'guiding' },
    })
  })

  it('maps a synthesis backend response to synthesis review', () => {
    const update = buildBackendTurnStateUpdate({
      session: { stage: 'synthesis', state: 'validating' },
      coach_message: 'Here is the synthesis.',
    })

    expect(update.uiScreen).toBe('synthesis_review')
  })

  it('caches coach_message for pathway responses', () => {
    const update = buildBackendTurnStateUpdate(
      {
        session: { stage: 'pathways', state: 'presenting' },
        coach_message: '## Pathway\nDetails',
      },
      'older pathways',
    )

    expect(update.cachedPathwaysMessage).toBe('## Pathway\nDetails')
  })

  it('preserves existing cached pathways for non-pathway responses', () => {
    const update = buildBackendTurnStateUpdate(
      {
        session: { stage: 'coaching', state: 'guiding' },
        coach_message: 'Next question.',
      },
      'existing pathways',
    )

    expect(update.cachedPathwaysMessage).toBe('existing pathways')
  })
})

describe('buildMissingSessionResetState', () => {
  it('builds the missing-session reset state', () => {
    const resetState = buildMissingSessionResetState({
      sessionId: 'abc',
      sessionView: { stage: 'coaching' },
      coachMessage: 'reply',
      cachedPathwaysMessage: 'cached',
      debugHistory: [{ turn: 1 }],
      latestDebug: { turn: 1 },
      latestDebugFingerprint: 'fingerprint',
      awaitingPathwaysAfterRefinement: true,
      problemInputVersion: 3,
      coachingInputVersion: 4,
      synthesisFeedbackVersion: 5,
      pathwaysSelectionVersion: 6,
      frontendError: 'error',
    })

    expect(resetState).toMatchObject({
      sessionId: null,
      sessionView: null,
      coachMessage: '',
      cachedPathwaysMessage: '',
      debugHistory: [],
      latestDebug: null,
      latestDebugFingerprint: null,
      awaitingPathwaysAfterRefinement: false,
      uiScreen: 'intro',
      problemInputVersion: 4,
      coachingInputVersion: 5,
      synthesisFeedbackVersion: 6,
      pathwaysSelectionVersion: 7,
      frontendError: null,
      frontendNotice: MISSING_SESSION_NOTICE,
    })
  })
})
