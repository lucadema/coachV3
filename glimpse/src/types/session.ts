export type BackendStage =
  | 'classification'
  | 'coaching'
  | 'synthesis'
  | 'pathways'
  | 'closure'
  | (string & {})

export type FrontendScreen =
  | 'welcome'
  | 'confidentiality'
  | 'intro'
  | 'problem_input'
  | 'coaching'
  | 'synthesis_review'
  | 'pathways'
  | 'pathways_review'
  | 'feedback'
  | 'closed'

export type BackendSessionView = {
  session_id?: string | null
  stage?: BackendStage | null
  state?: string | null
  cancelled?: boolean
  completed?: boolean
  [key: string]: unknown
}

export type BackendTurnResponse = {
  session?: BackendSessionView
  coach_message?: string | null
  [key: string]: unknown
}

export type FrontendSessionState = {
  uiScreen: FrontendScreen
  sessionId: string | null
  sessionView: BackendSessionView | null
  coachMessage: string
  cachedPathwaysMessage: string
  debugHistory: unknown[]
  latestDebug: unknown | null
  latestDebugFingerprint: string | null
  frontendError: string | null
  frontendNotice: string | null
  awaitingPathwaysAfterRefinement: boolean
  problemInputVersion: number
  coachingInputVersion: number
  synthesisFeedbackVersion: number
  pathwaysSelectionVersion: number
}

export type BackendTurnStateUpdate = Pick<
  FrontendSessionState,
  'sessionView' | 'coachMessage' | 'uiScreen' | 'cachedPathwaysMessage'
>

export type MissingSessionResetState = Omit<FrontendSessionState, 'uiScreen'> & {
  uiScreen: 'intro'
}

export type PathwayCard = {
  title: string
  body: string
}
