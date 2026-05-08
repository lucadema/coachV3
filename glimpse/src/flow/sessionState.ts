import type {
  BackendSessionView,
  BackendTurnResponse,
  BackendTurnStateUpdate,
  FrontendSessionState,
  MissingSessionResetState,
} from '../types/session'
import { mapBackendToScreen } from './sessionFlow'

export const MISSING_SESSION_NOTICE =
  'Your previous session is no longer available, likely because the backend restarted or was redeployed. Please start a new session.'

export function defaultFrontendState(): FrontendSessionState {
  return {
    uiScreen: 'welcome',
    sessionId: null,
    sessionView: null,
    coachMessage: '',
    cachedPathwaysMessage: '',
    debugHistory: [],
    latestDebug: null,
    latestDebugFingerprint: null,
    frontendError: null,
    frontendNotice: null,
    awaitingPathwaysAfterRefinement: false,
    problemInputVersion: 0,
    coachingInputVersion: 0,
    synthesisFeedbackVersion: 0,
    pathwaysSelectionVersion: 0,
  }
}

export function buildCachedPathwaysMessage(
  session: BackendSessionView,
  coachMessage: string,
  currentCachedPathwaysMessage = '',
): string {
  if (session.stage === 'pathways' && coachMessage) {
    return coachMessage
  }

  return currentCachedPathwaysMessage
}

export function buildBackendTurnStateUpdate(
  data: BackendTurnResponse,
  currentCachedPathwaysMessage = '',
): BackendTurnStateUpdate {
  const session = data.session ?? {}
  const coachMessage = data.coach_message ?? ''

  return {
    sessionView: session,
    coachMessage,
    uiScreen: mapBackendToScreen(session),
    cachedPathwaysMessage: buildCachedPathwaysMessage(
      session,
      coachMessage,
      currentCachedPathwaysMessage,
    ),
  }
}

export function buildMissingSessionResetState(
  currentState: Partial<FrontendSessionState> = {},
): MissingSessionResetState {
  return {
    sessionId: null,
    sessionView: null,
    coachMessage: '',
    cachedPathwaysMessage: '',
    debugHistory: [],
    latestDebug: null,
    latestDebugFingerprint: null,
    frontendError: null,
    frontendNotice: MISSING_SESSION_NOTICE,
    awaitingPathwaysAfterRefinement: false,
    uiScreen: 'intro',
    problemInputVersion: (currentState.problemInputVersion ?? 0) + 1,
    coachingInputVersion: (currentState.coachingInputVersion ?? 0) + 1,
    synthesisFeedbackVersion: (currentState.synthesisFeedbackVersion ?? 0) + 1,
    pathwaysSelectionVersion: (currentState.pathwaysSelectionVersion ?? 0) + 1,
  }
}
