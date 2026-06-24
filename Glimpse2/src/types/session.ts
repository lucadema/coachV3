export type BackendStage =
  | 'classification'
  | 'coaching'
  | 'synthesis'
  | 'pathways'
  | 'closure'
  | (string & {})

export type ExperienceStep =
  | 'launch'
  | 'privacy'
  | 'intro'
  | 'problem_input'
  | 'coaching'
  | 'synthesis_review'
  | 'pathways'
  | 'feedback_query'
  | 'feedback'
  | 'closed'
  | 'backend_response'

export type FrontendScreen =
  | 'problem_input'
  | 'coaching'
  | 'synthesis_review'
  | 'pathways'
  | 'feedback'
  | 'closed'
  | 'backend_response'

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

export type PathwayCard = {
  title: string
  body: string
}

export type ConversationExchange = {
  id: string
  step: ExperienceStep
  userMessage: string
  coachMessage: string
  createdAt: string
}

export type SynthesisReviewMode =
  | 'review'
  | 'refinement_open'
  | 'awaiting_pathways_after_refinement'
